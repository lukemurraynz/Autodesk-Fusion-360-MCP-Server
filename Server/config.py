# Fusion 360 API Configuration

# Base URL für den Fusion 360 Server
BASE_URL = "http://localhost:5000"

# API Endpoints
ENDPOINTS = {
    "holes": f"{BASE_URL}/holes",
    "destroy": f"{BASE_URL}/destroy",
    "witzenmann": f"{BASE_URL}/Witzenmann",
    "spline": f"{BASE_URL}/spline",
    "sweep": f"{BASE_URL}/sweep",
    "undo": f"{BASE_URL}/undo",
    "count_parameters": f"{BASE_URL}/count_parameters",
    "list_parameters": f"{BASE_URL}/list_parameters",
    "export_step": f"{BASE_URL}/Export_STEP",
    "export_stl": f"{BASE_URL}/Export_STL",
    "fillet_edges": f"{BASE_URL}/fillet_edges",
    "change_parameter": f"{BASE_URL}/set_parameter",
    "draw_cylinder": f"{BASE_URL}/draw_cylinder",
    "draw_box": f"{BASE_URL}/Box",
    "shell_body": f"{BASE_URL}/shell_body",
    "draw_lines": f"{BASE_URL}/draw_lines",
    "extrude": f"{BASE_URL}/extrude_last_sketch",
    "extrude_thin": f"{BASE_URL}/extrude_thin",
    "cut_extrude": f"{BASE_URL}/cut_extrude",
    "revolve": f"{BASE_URL}/revolve",
    "draw_arc": f"{BASE_URL}/arc",
    "draw_one_line": f"{BASE_URL}/draw_one_line",
    "circular_pattern": f"{BASE_URL}/circular_pattern",
    "ellipsie": f"{BASE_URL}/ellipsis",
    "draw2Dcircle": f"{BASE_URL}/create_circle",
    "loft": f"{BASE_URL}/loft",
    "test_connection": f"{BASE_URL}/test_connection",
    "draw_sphere": f"{BASE_URL}/sphere",
    "threaded": f"{BASE_URL}/threaded",
    "delete_everything": f"{BASE_URL}/delete_everything",
    "boolean_operation": f"{BASE_URL}/boolean_operation",
    "draw_2d_rectangle": f"{BASE_URL}/draw_2d_rectangle",
    "rectangular_pattern": f"{BASE_URL}/rectangular_pattern",
    "draw_text": f"{BASE_URL}/draw_text",
    "move_body": f"{BASE_URL}/move_body",
    "pocket_recess": f"{BASE_URL}/pocket_recess",
    "sketch_on_face": f"{BASE_URL}/sketch_on_face",
    "create_work_plane": f"{BASE_URL}/create_work_plane",
    "project_edges": f"{BASE_URL}/project_edges",
    "draw_polygon": f"{BASE_URL}/draw_polygon",
    "offset_surface": f"{BASE_URL}/offset_surface",
    "mirror_feature": f"{BASE_URL}/mirror_feature",
    "list_bodies": f"{BASE_URL}/list_bodies",
    "get_active_body": f"{BASE_URL}/get_active_body",
    "rename_body": f"{BASE_URL}/rename_body",
    "list_sketches": f"{BASE_URL}/list_sketches",
    "get_active_sketch": f"{BASE_URL}/get_active_sketch",
    "activate_sketch": f"{BASE_URL}/activate_sketch",
    "close_sketch": f"{BASE_URL}/close_sketch",
    "select_body": f"{BASE_URL}/select_body",
    "select_sketch": f"{BASE_URL}/select_sketch",

    # NEW ENHANCED TOOLS - Phase 1-4
    "get_sketch_status": f"{BASE_URL}/get_sketch_status",
    "list_faces": f"{BASE_URL}/list_faces",
    "pocket_recess_safe": f"{BASE_URL}/pocket_recess_safe",
    "get_feature_history": f"{BASE_URL}/get_feature_history",
    "find_face_by_property": f"{BASE_URL}/find_face_by_property",
    "draw_rectangles_batch": f"{BASE_URL}/draw_rectangles_batch",
    "pocket_smart": f"{BASE_URL}/pocket_smart",
    "begin_transaction": f"{BASE_URL}/begin_transaction",
    "commit_transaction": f"{BASE_URL}/commit_transaction",
    "rollback_transaction": f"{BASE_URL}/rollback_transaction",
    "get_operation_log": f"{BASE_URL}/get_operation_log",
    "create_sketch_on_body_plane": f"{BASE_URL}/create_sketch_on_body_plane",
    "validate_face_exists": f"{BASE_URL}/validate_face_exists",
    "select_faces_by_semantic": f"{BASE_URL}/select_faces_by_semantic",
    "clear_sketch": f"{BASE_URL}/clear_sketch",
    "extrude_safe": f"{BASE_URL}/extrude_safe",

    # PROP PERFECTION TOOLS
    "chamfer_edges": f"{BASE_URL}/chamfer_edges",
    "split_body": f"{BASE_URL}/split_body",
    "scale_body": f"{BASE_URL}/scale_body",

}

# Request Headers
HEADERS = {
    "Content-Type": "application/json"
}

# Timeouts (in Sekunden)
REQUEST_TIMEOUT = 30
RETRY_DELAY = 2  # Seconds to wait between retry attempts
