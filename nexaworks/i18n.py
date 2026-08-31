LANG_CODE = {
    "English": "en",
    "Tiếng Việt": "vi",
    "日本語": "ja",
}

TRANSLATIONS = {
    "English": {
        "title": "NexaWorks Operations Decision Support Tool",
        "upload": "Dataset (candidate_dataset.json)",
        "load": "Load dataset",
        "strict": "Strict cash constraint",
        "time": "Solver time limit (s)",
        "run": "Run optimization",
        "restore": "Restore initial scenario",
        "status": "Status",
        "decision": "Decision",
        "assignment": "Assignment",
        "sales": "Commercial options",
        "explain": "Decision explanation",
        "warnings": "Warnings / validation / infeasibility diagnostics",
        "patch": "Scenario patch (JSON)",
        "apply": "Apply patch",
        "save": "Save scenario + plan",
        "language": "Language",
        "loaded": "Loaded",
        "need_load": "Please load dataset first",
        "patched": "Patch applied",
        "restored": "Restored initial scenario",
        "saved": "Saved",

        "selected_by_objective": "Selected by objective under current constraints",
        "not_selected": "Not selected under current objective/constraints",
        "mandatory": "Mandatory",
        "committed": "Committed",
        "depends_on": "Depends on",
        "assigned": "Assigned",
        "starts_later": "Starts {hours} hours later",

        "true": "Yes",
        "false": "No",

        "feasible": "Feasible",
        "infeasible": "Infeasible",
        "warning": "Warning",
        "invalid_input": "Invalid Input",

        "no_solution": "No feasible solution returned",
        "capacity_overload": "Capacity overload",
        "deadline_violation": "Deadline violation",
        "dependency_violation": "Dependency violation",
        "resource_overload": "Shared-resource overload",
        "cash_shortfall": "Cash shortfall",
        "no_skill_coverage": "No qualified skill coverage",
        "no_language_coverage": "No qualified language coverage",
    },

    "Tiếng Việt": {
        "title": "Công cụ hỗ trợ quyết định vận hành NexaWorks",
        "upload": "Dữ liệu (candidate_dataset.json)",
        "load": "Nạp dữ liệu",
        "strict": "Ràng buộc tiền mặt cứng",
        "time": "Giới hạn thời gian solver (giây)",
        "run": "Chạy tối ưu hóa",
        "restore": "Khôi phục kịch bản ban đầu",
        "status": "Trạng thái",
        "decision": "Quyết định",
        "assignment": "Phân công",
        "sales": "Phương án thương mại",
        "explain": "Giải thích quyết định",
        "warnings": "Cảnh báo / kiểm tra / chẩn đoán không khả thi",
        "patch": "Thay đổi kịch bản (JSON)",
        "apply": "Áp dụng thay đổi",
        "save": "Lưu kịch bản + kế hoạch",
        "language": "Ngôn ngữ",
        "loaded": "Đã nạp",
        "need_load": "Vui lòng nạp dữ liệu trước",
        "patched": "Đã áp dụng thay đổi",
        "restored": "Đã khôi phục kịch bản ban đầu",
        "saved": "Đã lưu",

        "selected_by_objective": "Được chọn theo hàm mục tiêu và các ràng buộc hiện tại",
        "not_selected": "Không được chọn theo hàm mục tiêu và các ràng buộc hiện tại",
        "mandatory": "Bắt buộc",
        "committed": "Đã cam kết",
        "depends_on": "Phụ thuộc vào",
        "assigned": "Được phân công cho",
        "starts_later": "Bắt đầu muộn hơn {hours} giờ",

        "true": "Có",
        "false": "Không",

        "feasible": "Khả thi",
        "infeasible": "Không khả thi",
        "warning": "Cảnh báo",
        "invalid_input": "Dữ liệu đầu vào không hợp lệ",

        "no_solution": "Không tìm thấy phương án khả thi",
        "capacity_overload": "Vượt quá năng lực",
        "deadline_violation": "Vi phạm thời hạn",
        "dependency_violation": "Vi phạm phụ thuộc",
        "resource_overload": "Quá tải tài nguyên dùng chung",
        "cash_shortfall": "Thiếu hụt tiền mặt",
        "no_skill_coverage": "Không có nhân sự đáp ứng kỹ năng",
        "no_language_coverage": "Không có nhân sự đáp ứng ngôn ngữ",
    },

    "日本語": {
        "title": "NexaWorks 運用意思決定支援ツール",
        "upload": "データセット (candidate_dataset.json)",
        "load": "データを読み込む",
        "strict": "厳格なキャッシュ制約",
        "time": "ソルバー制限時間（秒）",
        "run": "最適化を実行",
        "restore": "初期シナリオに戻す",
        "status": "ステータス",
        "decision": "意思決定",
        "assignment": "担当割当",
        "sales": "商用オプション",
        "explain": "意思決定の説明",
        "warnings": "警告 / 検証 / 実行不可能診断",
        "patch": "シナリオ変更 (JSON)",
        "apply": "変更を適用",
        "save": "シナリオ + 計画を保存",
        "language": "言語",
        "loaded": "読み込み完了",
        "need_load": "先にデータを読み込んでください",
        "patched": "変更を適用しました",
        "restored": "初期シナリオに戻しました",
        "saved": "保存しました",

        "selected_by_objective": "現在の目的関数と制約に基づいて選択",
        "not_selected": "現在の目的関数と制約により選択されていません",
        "mandatory": "必須",
        "committed": "契約済み",
        "depends_on": "依存先",
        "assigned": "担当",
        "starts_later": "{hours}時間後に開始",

        "true": "はい",
        "false": "いいえ",

        "feasible": "実行可能",
        "infeasible": "実行不可能",
        "warning": "警告",
        "invalid_input": "入力データが不正です",

        "no_solution": "実行可能な解が見つかりません",
        "capacity_overload": "能力超過",
        "deadline_violation": "期限違反",
        "dependency_violation": "依存関係違反",
        "resource_overload": "共有リソース超過",
        "cash_shortfall": "キャッシュ不足",
        "no_skill_coverage": "必要なスキルを満たす担当者がいません",
        "no_language_coverage": "必要な言語を満たす担当者がいません",
    },
}


COLUMN_TRANSLATIONS = {
    "English": {
        "work_id": "Work ID",
        "title": "Title",
        "selected": "Selected",
        "decision": "Decision",
        "person_id": "Person ID",
        "assigned_hours": "Assigned hours",
        "start_hour": "Start hour",
        "end_hour": "End hour",
        "option_id": "Option ID",
        "label": "Label",
        "price_jpy": "Price (JPY)",
        "win_probability": "Win probability",
        "expected_margin_jpy": "Expected margin (JPY)",
        "delivery_hours": "Delivery hours",
        "payment_days": "Payment days",
        "cash_in_horizon_jpy": "Cash in horizon (JPY)",
        "warranty_months": "Warranty (months)",
        "follow_on_value_jpy": "Follow-on value (JPY)",
        "integrated_utility": "Integrated utility",
        "selected_by_solver": "Selected by solver",
        "reason": "Reason",
        "risk_penalty_jpy": "Risk penalty (JPY)",
        "customer_value_jpy": "Customer value (JPY)",
        "labor_cost_jpy": "Labor cost (JPY)",
        "delay_penalty_jpy": "Delay penalty (JPY)",
        "effective_hours": "Effective hours",
        "warnings": "Warnings",
        "code": "Code",
        "status": "Status",
        "entity": "Entity",
        "record_id": "Record ID",
        "field": "Field",
        "message": "Message",
        "execute": "Execute",
        "delay": "Delay",
        "decline": "Decline",
    },

    "Tiếng Việt": {
        "execute": "Thực hiện",
        "delay": "Trì hoãn",
        "decline": "Từ chối",
        "true": "Có",
        "false": "Không",
        "CASH_SHORTFALL": "Thiếu hụt tiền mặt",
        "Expected cash {cash} < buffer {buffer}": "Tiền mặt dự kiến {cash} < Mức dự phòng {buffer}",

        "work_id": "Mã công việc",
        "title": "Tiêu đề",
        "selected": "Đã chọn",
        "decision": "Quyết định",
        "person_id": "Mã nhân sự",
        "assigned_hours": "Số giờ phân công",
        "start_hour": "Giờ bắt đầu",
        "end_hour": "Giờ kết thúc",
        "option_id": "Mã phương án",
        "label": "Tên phương án",
        "price_jpy": "Giá (JPY)",
        "win_probability": "Xác suất thắng",
        "expected_margin_jpy": "Biên lợi nhuận kỳ vọng (JPY)",
        "delivery_hours": "Số giờ thực hiện",
        "payment_days": "Số ngày thanh toán",
        "cash_in_horizon_jpy": "Tiền thu trong kỳ (JPY)",
        "warranty_months": "Bảo hành (tháng)",
        "follow_on_value_jpy": "Giá trị phát sinh (JPY)",
        "integrated_utility": "Giá trị tích hợp",
        "selected_by_solver": "Được solver chọn",
        "reason": "Lý do",
        "risk_penalty_jpy": "Chi phí rủi ro (JPY)",
        "customer_value_jpy": "Giá trị khách hàng (JPY)",
        "labor_cost_jpy": "Chi phí nhân công (JPY)",
        "delay_penalty_jpy": "Chi phí trì hoãn (JPY)",
        "effective_hours": "Số giờ hiệu dụng",
        "warnings": "Cảnh báo",
        "code": "Mã",
        "status": "Trạng thái",
        "entity": "Đối tượng",
        "record_id": "Mã bản ghi",
        "field": "Trường",
        "message": "Thông báo",
    },

    "日本語": {
        "execute": "実行",
        "delay": "保留",
        "decline": "見送り",
        "true": "はい",
        "false": "いいえ",

        "work_id": "作業ID",
        "title": "タイトル",
        "selected": "選択済み",
        "decision": "意思決定",
        "person_id": "担当者ID",
        "assigned_hours": "割当時間",
        "start_hour": "開始時間",
        "end_hour": "終了時間",
        "option_id": "オプションID",
        "label": "オプション名",
        "price_jpy": "価格（JPY）",
        "win_probability": "受注確率",
        "expected_margin_jpy": "期待利益（JPY）",
        "delivery_hours": "実行時間",
        "payment_days": "支払日数",
        "cash_in_horizon_jpy": "期間内入金（JPY）",
        "warranty_months": "保証期間（月）",
        "follow_on_value_jpy": "将来価値（JPY）",
        "integrated_utility": "統合効用",
        "selected_by_solver": "ソルバー選択",
        "reason": "理由",
        "risk_penalty_jpy": "リスクペナルティ（JPY）",
        "customer_value_jpy": "顧客価値（JPY）",
        "labor_cost_jpy": "人件費（JPY）",
        "delay_penalty_jpy": "遅延ペナルティ（JPY）",
        "effective_hours": "実効時間",
        "warnings": "警告",
        "code": "コード",
        "status": "ステータス",
        "entity": "対象",
        "record_id": "レコードID",
        "field": "項目",
        "message": "メッセージ",
    },
}


# Cột nội dung đa ngôn ngữ: ưu tiên lấy *_vi / *_en / *_ja theo UI
MULTILINGUAL_CONTENT_COLS = ("title", "label", "notes", "reason", "message")


def t(language, key, **kwargs):
    text = TRANSLATIONS.get(language, TRANSLATIONS["English"]).get(
        key,
        TRANSLATIONS["English"].get(key, key),
    )
    return text.format(**kwargs)


def _pick_lang_col(df, base_col, language):
    """Chọn cột base_col_<code> theo ngôn ngữ UI; fallback en rồi canonical."""
    code = LANG_CODE.get(language, "en")
    for suffix in (code, "en", "canonical"):
        col = f"{base_col}_{suffix}"
        if col in df.columns:
            return col
    return base_col if base_col in df.columns else None


def localize_dataframe(df, language):
    if df is None:
        return df

    result = df.copy()

    # 1) Thay nội dung title/label/... bằng bản dịch đúng ngôn ngữ
    for base in MULTILINGUAL_CONTENT_COLS:
        src = _pick_lang_col(result, base, language)
        if src and src != base and src in result.columns:
            result[base] = result[src]
        # Ẩn các cột phụ _en/_vi/_ja/_canonical khi hiển thị
        drop_cols = [
            c for c in result.columns
            if c.startswith(f"{base}_") and c != base
        ]
        if drop_cols:
            result = result.drop(columns=drop_cols, errors="ignore")

    # 2) Dịch tên cột
    mapping = COLUMN_TRANSLATIONS.get(language, COLUMN_TRANSLATIONS["English"])
    result = result.rename(columns={c: mapping.get(c, c) for c in result.columns})

    # 3) Dịch giá trị boolean / decision / status
    for col in result.columns:
        dtype_name = getattr(result[col].dtype, "name", str(result[col].dtype))
        if dtype_name in ("object", "string", "str", "bool", "boolean") or result[col].dtype == object:
            result[col] = result[col].map(lambda x: localize_value(x, language))

    return result


def localize_value(value, language):
    # bool / numpy.bool_
    if isinstance(value, (bool, type(True))) or type(value).__name__ in ("bool_", "bool8"):
        try:
            return t(language, "true" if bool(value) else "false")
        except Exception:
            pass

    if value in {"Feasible", "Infeasible", "Warning", "Invalid Input"}:
        key = {
            "Feasible": "feasible",
            "Infeasible": "infeasible",
            "Warning": "warning",
            "Invalid Input": "invalid_input",
        }[value]
        return t(language, key)

    if value in {"execute", "delay", "decline"}:
        mapping = COLUMN_TRANSLATIONS.get(language, COLUMN_TRANSLATIONS["English"])
        return mapping.get(value, value)

    return value