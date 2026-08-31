from __future__ import annotations

import pandas as pd
from ortools.sat.python import cp_model

from .financials import work_financials, option_financials


class NexaWorksEngine:
    """CP-SAT engine cho lựa chọn, phân công, lịch, sales option và cash."""

    def __init__(self, dm, raw, config):
        self.dm = dm
        self.raw = raw
        self.cfg = config
        self.work = dm["work_items"].copy()
        customers = dm["customers"].set_index("customer_id")
        self.work["customer_strategic_value"] = self.work["customer_id"].map(customers["strategic_value"]).fillna(0)
        self.work["customer_reference_value"] = self.work["customer_id"].map(customers["reference_value"]).fillna(0)

        self.people = dm["people"]
        self.people_ids = self.people["person_id"].tolist()
        self.work_ids = self.work["work_id"].tolist()
        self.cap = self.people.set_index("person_id")["capacity_hours"].astype(int).to_dict()
        self.cost = self.people.set_index("person_id")["hourly_cost_jpy"].astype(int).to_dict()
        self.skills = dm["person_skills"].set_index(["person_id", "skill"])["skill_level"].to_dict()
        self.langs = dm["person_languages"].groupby("person_id")["language"].apply(set).to_dict()
        self.work_row = self.work.set_index("work_id").to_dict("index")
        self.opts_by_work = {
            w: dm["commercial_options"].loc[dm["commercial_options"]["work_id"] == w, "option_id"].tolist()
            for w in self.work_ids
        }
        self.option_row = dm["commercial_options"].set_index("option_id").to_dict("index")
        self.model = None
        self.solver = None
        self.status = None

    def hstart(self, dt):
        """Đổi ngày thành hour-index tính từ planning_start."""
        start = pd.Timestamp(self.raw["metadata"]["planning_start"])
        return int((pd.Timestamp(dt) - start).days * self.cfg["hours_per_day"])

    def hend(self, dt):
        """Đổi due date thành mốc cuối horizon theo quy ước inclusive due date."""
        start = pd.Timestamp(self.raw["metadata"]["planning_start"])
        delta_days = (pd.Timestamp(dt) - start).days
        if self.cfg["inclusive_due_date"]:
            delta_days += 1
        return int(delta_days * self.cfg["hours_per_day"])

    def qualified_people_for_skill(self, skill, min_level):
        """Trả về các person có skill >= min_level."""
        return [p for p in self.people_ids if self.skills.get((p, skill), 0) >= min_level]

    def qualified_people_for_language(self, language):
        """Trả về các person có ngôn ngữ yêu cầu."""
        return [p for p in self.people_ids if language in self.langs.get(p, set())]

    def build(self):
        """Tạo CP-SAT model: variables + constraints + objective."""
        mdl = cp_model.CpModel()
        start_plan = pd.Timestamp(self.raw["metadata"]["planning_start"])
        end_plan = pd.Timestamp(self.raw["metadata"]["planning_end"])
        horizon_days = (end_plan - start_plan).days + 1
        T = horizon_days * self.cfg["hours_per_day"]

        self.select = {w: mdl.NewBoolVar(f"select_{w}") for w in self.work_ids}
        self.ws = {w: mdl.NewIntVar(0, T, f"ws_{w}") for w in self.work_ids}
        self.we = {w: mdl.NewIntVar(0, T, f"we_{w}") for w in self.work_ids}
        self.assign, self.hours = {}, {}
        self.start, self.end = {}, {}
        self.effective_hours = {}
        intervals = {p: [] for p in self.people_ids}

        for w in self.work_ids:
            r = self.work_row[w]
            if self.cfg["mandatory_is_hard"] and bool(r["mandatory"]):
                mdl.Add(self.select[w] == 1)

            earliest = self.hstart(r["earliest_start_dt"])
            due = min(T, self.hend(r["due_date_dt"]))
            mdl.Add(self.ws[w] >= earliest).OnlyEnforceIf(self.select[w])
            mdl.Add(self.we[w] <= due).OnlyEnforceIf(self.select[w])
            mdl.Add(self.we[w] >= self.ws[w] + self.select[w])

            # Base effort; commercial option will override this below.
            base_hours = int(r["required_hours"])
            eff = mdl.NewIntVar(0, max(base_hours, 1_000_000), f"effective_hours_{w}")
            self.effective_hours[w] = eff

            # Portfolio effect E002: if trigger + target are both selected,
            # require trigger first so the documented 25% reduction applies.
            reduction_applied = []
            for e in self.raw.get("portfolio_effects", []):
                effect = e.get("effect", {})
                if effect.get("type") != "hours_reduction" or w not in e.get("targets", []):
                    continue
                trigger = e["trigger"]
                if trigger not in self.select:
                    continue
                rate = float(effect.get("value", 0) or 0)
                reduced_hours = int(round(base_hours * rate))
                mdl.Add(self.we[trigger] <= self.ws[w]).OnlyEnforceIf([self.select[trigger], self.select[w]])
                z = mdl.NewBoolVar(f"apply_{e['id']}_{w}")
                mdl.Add(z <= self.select[trigger])
                mdl.Add(z <= self.select[w])
                mdl.Add(z >= self.select[trigger] + self.select[w] - 1)
                reduction_applied.append((reduced_hours, z))

            # Commercial options: selected option determines actual delivery hours.
            option_terms = []
            for oid in self.opts_by_work[w]:
                option_terms.append((int(self.option_row[oid]["delivery_hours"]), self.opt_var_placeholder(oid, mdl)))
            if option_terms:
                # option vars must exist before linking effective hours.
                option_vars = [var for _, var in option_terms]
                for var in option_vars:
                    mdl.Add(var <= self.select[w])
                mdl.Add(sum(option_vars) == self.select[w])
                chosen_hours = sum(hours * var for hours, var in option_terms)
                reduction_expr = sum(amount * z for amount, z in reduction_applied)
                mdl.Add(eff == chosen_hours - reduction_expr)
            else:
                reduction_expr = sum(amount * z for amount, z in reduction_applied)
                mdl.Add(eff == base_hours * self.select[w] - reduction_expr)

            # Person assignment + optional intervals.
            for p in self.people_ids:
                a = mdl.NewBoolVar(f"assign_{w}_{p}")
                h = mdl.NewIntVar(0, self.cap[p], f"hours_{w}_{p}")
                s = mdl.NewIntVar(0, T, f"start_{w}_{p}")
                e = mdl.NewIntVar(0, T, f"end_{w}_{p}")
                self.assign[(w, p)] = a
                self.hours[(w, p)] = h
                self.start[(w, p)] = s
                self.end[(w, p)] = e
                mdl.Add(h <= self.cap[p] * a)
                mdl.Add(h >= a)
                mdl.Add(s >= self.ws[w]).OnlyEnforceIf(a)
                mdl.Add(e <= self.we[w]).OnlyEnforceIf(a)
                mdl.Add(e == s + h).OnlyEnforceIf(a)
                mdl.Add(e == s).OnlyEnforceIf(a.Not())
                intervals[p].append(mdl.NewOptionalIntervalVar(s, h, e, a, f"iv_{w}_{p}"))

            mdl.Add(sum(self.hours[(w, p)] for p in self.people_ids) == eff)

            # Skill coverage: at least one qualified person must be assigned.
            for _, req in self.dm["work_skills"][self.dm["work_skills"]["work_id"] == w].iterrows():
                qualified = self.qualified_people_for_skill(req["skill"], int(req["min_level"]))
                if qualified:
                    mdl.Add(sum(self.assign[(w, p)] for p in qualified) >= self.select[w])
                else:
                    mdl.Add(self.select[w] == 0)

            # Language coverage.
            for language in self.dm["work_languages"].loc[self.dm["work_languages"]["work_id"] == w, "language"].tolist():
                qualified = self.qualified_people_for_language(language)
                if qualified:
                    mdl.Add(sum(self.assign[(w, p)] for p in qualified) >= self.select[w])
                else:
                    mdl.Add(self.select[w] == 0)

        # Capacity + no-overlap + unavailability.
        for p in self.people_ids:
            mdl.Add(sum(self.hours[(w, p)] for w in self.work_ids) <= self.cap[p])
            fixed_intervals = []
            for _, u in self.dm["person_unavailability"][self.dm["person_unavailability"]["person_id"] == p].iterrows():
                s = self.hstart(u["start_date"])
                e = self.hend(u["end_date"])
                fixed_intervals.append(mdl.NewFixedSizeIntervalVar(s, e - s, f"unavailable_{p}_{s}"))
            mdl.AddNoOverlap(intervals[p] + fixed_intervals)

        # Dependencies.
        for _, dep in self.dm["work_dependencies"].iterrows():
            succ, pred = dep["work_id"], dep["depends_on_work_id"]
            if succ in self.select and pred in self.select:
                mdl.Add(self.select[succ] <= self.select[pred])
                mdl.Add(self.we[pred] <= self.ws[succ]).OnlyEnforceIf([self.select[pred], self.select[succ]])

        # Conflicts.
        for _, conflict in self.dm["work_conflicts"].iterrows():
            a, b = conflict["work_id"], conflict["conflicts_with_work_id"]
            if a in self.select and b in self.select:
                mdl.Add(self.select[a] + self.select[b] <= 1)

        # Commercial option dependencies (e.g. W007-B requires W022).
        for _, dep in self.dm["option_dependencies"].iterrows():
            oid, prerequisite = dep["option_id"], dep["depends_on_work_id"]
            if oid in self.opt and prerequisite in self.select:
                mdl.Add(self.opt[oid] <= self.select[prerequisite])

        # Shared resource capacity is horizon-level because source data only gives total capacity.
        for _, resource in self.dm["shared_resources"].iterrows():
            rid = resource["resource_id"]
            cap = int(resource["capacity_hours"])
            demand = self.dm["work_resources"].loc[
                self.dm["work_resources"]["resource_id"] == rid
            ].groupby("work_id")["hours"].sum().to_dict()
            mdl.Add(sum(int(demand.get(w, 0)) * self.select[w] for w in self.work_ids) <= cap)

        # Cash: horizon-level expected cash. Payments after planning_end are not counted as horizon inflow.
        company = self.dm["company"].iloc[0]
        base_cash = int(company["starting_cash_jpy"] - company["fixed_cash_outflow_jpy"])
        labor_cost = sum(self.hours[(w, p)] * int(self.cost[p]) for w in self.work_ids for p in self.people_ids)

        inflows, direct_costs = [], []
        for w in self.work_ids:
            r = self.work_row[w]
            if self.opts_by_work[w]:
                for oid in self.opts_by_work[w]:
                    o = self.option_row[oid]
                    if float(o["payment_days"]) <= (pd.Timestamp(self.raw["metadata"]["planning_end"]) - pd.Timestamp(self.raw["metadata"]["planning_start"])).days + 1:
                        inflows.append(int(round(float(o["price_jpy"]) * float(o["estimated_win_probability"]))) * self.opt[oid])
                    direct_costs.append(int(round(float(o["direct_cost_jpy"]) * float(o["estimated_win_probability"]))) * self.opt[oid])
            else:
                p = float(r["success_probability"])
                if r["cash_in_days"] is not None and float(r["cash_in_days"]) <= (pd.Timestamp(self.raw["metadata"]["planning_end"]) - pd.Timestamp(self.raw["metadata"]["planning_start"])).days + 1:
                    inflows.append(int(round(float(r["revenue_jpy"]) * p)) * self.select[w])
                direct_costs.append(int(round(float(r["direct_cost_jpy"]) * p)) * self.select[w])

        # E005: overdue receivable is cash collection, not revenue.
        for effect in self.raw.get("portfolio_effects", []):
            if effect["id"] == "E005" and effect["trigger"] in self.select:
                inflows.append(int(round((effect["effect"].get("probability") or 0) * (effect["effect"].get("value_jpy") or 0))) * self.select[effect["trigger"]])

        self.cash_expr = base_cash + sum(inflows) - labor_cost - sum(direct_costs)
        buffer = int(company["minimum_cash_buffer_jpy"])
        # Baseline: soft cash buffer. Strict scenario có thể bật hard constraint.
        self.cash_shortfall = mdl.NewIntVar(0, 1_000_000_000, "cash_shortfall")
        mdl.Add(self.cash_shortfall >= buffer - self.cash_expr)
        mdl.Add(self.cash_shortfall >= 0)
        if self.cfg["cash_hard_constraint"]:
            mdl.Add(self.cash_shortfall == 0)

        # Delay variable.
        self.delay = {}
        for w in self.work_ids:
            r = self.work_row[w]
            earliest = self.hstart(r["earliest_start_dt"])
            d = mdl.NewIntVar(0, T, f"delay_{w}")
            mdl.Add(d >= self.ws[w] - earliest - T * (1 - self.select[w]))
            mdl.Add(d <= T * self.select[w])
            self.delay[w] = d

        # Objective.
        terms = []
        # Phạt phần thiếu cash buffer nếu đang ở baseline soft-cash.
        terms.append(-int(self.cfg["cash_shortfall_weight_jpy_per_jpy"]) * self.cash_shortfall)
        for w in self.work_ids:
            r = self.work_row[w]
            cust_value = float(r["strategic_value"] + r["customer_strategic_value"] + r["customer_reference_value"]) * self.cfg["customer_point_jpy"]
            margin, risk = work_financials(r, self.cfg)
            coef = margin + cust_value - self.cfg["risk_weight"] * risk
            terms.append(int(round(coef)) * self.select[w])

        for oid, o in self.option_row.items():
            terms.append(int(round(option_financials(o, self.cfg))) * self.opt[oid])

        for w in self.work_ids:
            terms.append(-int(self.cfg["delay_weight_jpy_per_hour"]) * self.delay[w])
            for p in self.people_ids:
                terms.append(-int(self.cost[p] + self.cfg["labor_effort_weight_jpy_per_hour"]) * self.hours[(w, p)])

        mdl.Maximize(sum(terms))
        self.model = mdl
        return self

    def opt_var_placeholder(self, oid, mdl):
        """Tạo option BoolVar một lần và tái sử dụng trong mọi constraint."""
        if not hasattr(self, "opt"):
            self.opt = {}
        if oid not in self.opt:
            self.opt[oid] = mdl.NewBoolVar(f"option_{oid}")
        return self.opt[oid]

    def solve(self, time_limit=30, workers=8, seed=42):
        """Chạy solver với seed cố định để kết quả có thể tái lập."""
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.num_search_workers = workers
        solver.parameters.random_seed = seed
        status = solver.Solve(self.model)
        self.solver, self.status = solver, status
        feasible = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        return {
            "solver_status": solver.StatusName(status),
            "objective_value": solver.ObjectiveValue() if feasible else None,
            "best_bound": solver.BestObjectiveBound() if feasible else None,
        }

    def result(self):
        """Đọc nghiệm CP-SAT thành 4 bảng: decision, assignment, schedule, commercial_option."""
        if self.solver is None or self.status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return {
                "decision": pd.DataFrame(), "assignment": pd.DataFrame(),
                "schedule": pd.DataFrame(), "commercial_option": pd.DataFrame(),
                "objective_value": None, "solver_status": None, "cash_end_actual_jpy": None, "cash_end_expected_jpy": None, "cash_shortfall_jpy": None,
            }

        s = self.solver
        drows, arows, srows, orows = [], [], [], []
        for w in self.work_ids:
            selected = s.Value(self.select[w]) == 1
            delay = s.Value(self.delay[w])
            decision = "decline" if not selected else ("delay" if delay > 0 else "execute")
            wr = self.work_row[w]
            drows.append({
                "work_id": w,
                "title": wr.get("title_canonical", wr.get("title")),
                "title_en": wr.get("title_en", wr.get("title_canonical")),
                "title_vi": wr.get("title_vi", wr.get("title_canonical")),
                "title_ja": wr.get("title_ja", wr.get("title_canonical")),
                "decision": decision,
                "selected": selected,
                "mandatory": bool(wr["mandatory"]),
                "committed": bool(wr["committed"]),
                "base_hours": int(wr["required_hours"]),
                "effective_hours": s.Value(self.effective_hours[w]),
                "start_hour": s.Value(self.ws[w]),
                "end_hour": s.Value(self.we[w]),
                "delay_hours": delay,
            })
            for p in self.people_ids:
                h = s.Value(self.hours[(w, p)])
                if h > 0:
                    arows.append({"work_id": w, "person_id": p, "assigned_hours": h, "labor_cost_jpy": h * self.cost[p]})
                    srows.append({"work_id": w, "person_id": p, "start_hour": s.Value(self.start[(w, p)]), "end_hour": s.Value(self.end[(w, p)]), "assigned_hours": h})
            for oid in self.opts_by_work[w]:
                if s.Value(self.opt[oid]) == 1:
                    row = dict(self.option_row[oid])
                    row["option_id"] = oid
                    row["chosen"] = True
                    orows.append(row)

        return {
            "decision": pd.DataFrame(drows),
            "assignment": pd.DataFrame(arows),
            "schedule": pd.DataFrame(srows),
            "commercial_option": pd.DataFrame(orows),
            "objective_value": s.ObjectiveValue(),
            # cash_end_actual_jpy giữ giá trị tài chính thật để không làm sai giải thích.
            "cash_end_actual_jpy": s.Value(self.cash_expr),
            # Yêu cầu đầu ra: không âm và nhỏ hơn minimum buffer (JPY nguyên).
            # Chỉ dùng metric này cho hiển thị/tương thích; solver vẫn dùng cash_expr thật.
            "cash_end_expected_jpy": s.Value(self.cash_expr),
            "cash_shortfall_jpy": s.Value(self.cash_shortfall),
            "solver_status": s.StatusName(self.status),
        }