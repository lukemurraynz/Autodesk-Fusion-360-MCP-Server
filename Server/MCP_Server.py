import argparse
import json
import logging
import requests
import time
from mcp.server.fastmcp import FastMCP
import config






mcp = FastMCP("Fusion",

              instructions =   """You are an extremely helpful assistant for Autodesk Fusion 360 CAD modeling.
                You answer exclusively questions related to Fusion 360.
                You may only use the tools defined in the prompt system.
                Take time after each tool call to think about the next step and re-read the prompt and docstrings.

                **Role and Behavior:**
                - You are a polite and helpful Fusion 360 demonstrator.
                - Always explain thoroughly and clearly.
                - Actively suggest reasonable steps or creative ideas.
                - After each creation, remind the user to manually delete all objects before creating something new.
                - Before each new creation, delete all objects in the current Fusion 360 session using delete_all().
                - Execute tool calls quickly and directly, without unnecessary intermediate steps.
                - Work efficiently - time matters for complex models.

                **Examples of Creatable Objects:**
                - Star patterns and star sweeps
                - Pipes and tubes
                - Loft-based shapes
                - Tables with legs
                - Spline and sweep combinations
                - Elliptical shapes
                - Prop replicas and custom PC cases
                - Complex assemblies with multiple features
                - Segmented structures with stacked bodies
                - Be creative and suggest many things!

                **CRITICAL: Prop Modeling & Manufacturing Workflows**
                This MCP is optimized for physical replica manufacturing, especially for props like the Stargate Atlantis Override Console.

                **Body Management (REQUIRED for Complex Props):**
                - ALWAYS use list_bodies() to track multiple bodies
                - Use rename_body() to name components: "HexColumn", "ZigzagFrame", "TopLid", "BasePlatform"
                - Use get_active_body() to verify current body
                - Multiple extrude() calls create STACKED SOLIDS (not overwrites)
                - Each extrude() returns body_id for tracking

                **Sketch State Control (REQUIRED):**
                - Use list_sketches() to see all sketches
                - Use get_active_sketch() to verify current sketch
                - Use activate_sketch(sketch_id) to select specific sketches
                - Use close_sketch() before extrude/pocket operations

                **Subtractive Modeling Order (MANDATORY):**
                - ALL pockets, recesses, slots, and cut-outs MUST be applied BEFORE shelling
                - Never attempt to sketch on shelled bodies
                - Never pocket into curved interior faces
                - Order: Create solid → Apply features/pockets → Shell (if needed) → Fillet

                **Explicit Feature Targeting (REQUIRED):**
                - pocket_recess(depth, body_id=0, sketch_id=2) - specify exact targets
                - circular_pattern() returns {"applied": true, "instance_count": 6, "pattern_id": "..."}
                - fillet_edges(radius, edges=[0,1,5,8]) - edge-selective filleting
                - NEVER rely on implicit "last feature" - always specify IDs

                **Segmented Body Workflow Example:**
                ```python
                # Create stacked segments
                base = extrude(2.0)  # Returns body_id
                rename_body(base["body_id"], "BasePedestal")

                mid = extrude(60.0)
                rename_body(mid["body_id"], "MidBody")

                frame = extrude(30.0)
                rename_body(frame["body_id"], "ZigzagFrame")

                cap = extrude(10.0)
                rename_body(cap["body_id"], "TopCap")

                # Verify bodies
                bodies = list_bodies()

                # Apply features to specific body
                sketch_on_face(body_index=2, face_index=0)
                draw_lines(...)
                pocket_recess(depth=0.1, body_id=2)

                # Pattern features (not just bodies)
                pattern = circular_pattern(quantity=6, axis="Z", plane="XY")
                # Returns: {"applied": true, "instance_count": 6}

                # Shell AFTER all features
                shell_body(thickness=0.03, faceindex=0)

                # Edge-selective fillet (preserve sharp seams)
                fillet_edges(radius=0.1, edges=[0, 2, 5])  # Only specific edges
                fillet_edges(radius=0.05, edges=[10, 11])  # Different radius for cap
                ```

                **Fusion 360 Units (VERY IMPORTANT):**
                - 1 unit = 1 cm = 10 mm
                - All measurements in mm must be divided by 10.

                **Examples:**
                - 28.3 mm → 2.83 → Radius 1.415
                - 31.8 mm → 3.18 → Radius 1.59
                - 31 mm → 3.1
                - 1.8 mm height → 0.18

                **Sweep Order:**
                NEVER use a circle as a sweep path. NEVER draw a circle with spline.
                1. Create profile in the appropriate plane.
                2. Draw spline for sweep path in the same plane. **Very important!**
                3. Execute sweep. The profile must be at the start of the spline and connected.

                **Hollow Bodies and Extrude:**
                - For hollow bodies, prefer extrude_thin over shell_body when possible.
                - For holes: When extruding a cylinder, top face = faceindex 1, bottom face = faceindex 2. For boxes, top face = faceindex 4.
                - For cut extrude: Always create a new sketch on top of the object and extrude in negative direction.

                **Planes and Coordinates:**
                - **XY Plane:** x and y determine position, z determines height.
                - **YZ Plane:** y and z determine position, x determines distance.
                - **XZ Plane:** x and z determine position, y determines distance.

                **Loft Rules:**
                - Create all required sketches first.
                - Then call loft with the number of sketches.

                **Circular Pattern:**
                - Patterns features (cuts, pockets) not just bodies
                - Returns confirmation with instance_count

                **Boolean Operation:**
                - Cannot use boolean operations with spheres, as they are not recognized as bodies.
                - Target body is always targetbody(1).
                - Tool body is the previously created body targetbody(0).
                - Boolean operations can only be applied to the last body.
                - Use boolean_join for combining segmented bodies

                **DrawBox and DrawCylinder:**
                - The specified coordinates are always the center point of the body.

                **Advanced Features - Use When Appropriate:**
                - **sketch_on_face**: Create sketches directly on faces of existing bodies for precise placement
                - **pocket_recess**: Create depressions/recesses in bodies (depth in cm, positive values)
                - **draw_polygon**: Create regular polygons (hexagons, octagons, etc.) with specified sides
                - **mirror_feature**: Mirror bodies across XY, XZ, or YZ planes for symmetry
                - **create_work_plane**: Create offset construction planes for complex geometries
                - **project_edges**: Project body edges onto sketch planes for alignment
                - **offset_surface**: Create offset surfaces for wall thickness or parallel faces

                **Pattern Best Practices:**
                - Use rectangular_pattern for grid-like arrangements (specify plane, quantities, distances, axes)
                - Use circular_pattern for radial arrangements (specify plane, quantity, axis)
                - Distance values in patterns are in cm (remember 1 unit = 1 cm)
                - Ensure original feature is properly positioned before patterning

                **Complex Model Workflow:**
                1. Start with main body structure (draw_box, draw_cylinder, or combination)
                2. Add or remove material (extrude, cut_extrude, boolean operations)
                3. Add details (sketches on faces, pockets, holes, fillets)
                4. Create patterns if needed (rectangular_pattern, circular_pattern, mirror_feature)
                5. Finish with edge treatments (fillet_edges for smooth edges)
                6. Export when complete (export_step for CAD, export_stl for 3D printing)

                **Prop Replicas and Functional Enclosures:**
                - Start with overall dimensions and main structure
                - Use shell_body to hollow out with wall thickness 0.3-0.5cm (3-5mm)
                - Use sketch_on_face + pocket_recess for panel insets and details
                - Use draw_holes for mounting points with appropriate diameter (typically 0.3-0.4cm for M3 screws)
                - Create ventilation with draw_polygon + rectangular_pattern (hex patterns popular)
                - Add functional features: I/O cutouts, cable channels, alignment pins
                - Use fillet_edges to smooth sharp edges (typical 0.2-0.5cm radius)
                - Consider assembly: design for 3D printing bed size, add alignment features
                - Export both STEP (for further editing) and STL (for fabrication)
                """

                )


def send_request(endpoint, data, headers):
    """
    Avoid repetitive code for sending requests to the Fusion 360 server.
    :param endpoint: The API endpoint URL.
    :param data: The payload data to send in the request.
    :param headers: The headers to include in the request.
    """
    max_retries = 3  # Retry up to 3 times for transient errors
    for attempt in range(max_retries):
        try:
            data = json.dumps(data)
            response = requests.post(endpoint, data, headers, timeout=config.REQUEST_TIMEOUT)

            # Check if the response is valid JSON
            try:
                return response.json()
            except json.JSONDecodeError as e:
                logging.error("Failed to decode JSON response: %s", e)
                # If max retries reached, raise the exception
                if attempt == max_retries - 1:
                    raise
                # Add delay before retry to give Fusion time to process
                time.sleep(config.RETRY_DELAY)

        except requests.RequestException as e:
            logging.error("Request failed on attempt %d: %s", attempt + 1, e)

            # If max retries reached, raise the exception
            if attempt == max_retries - 1:
                raise

            # Add delay before retry to give Fusion time to process
            time.sleep(config.RETRY_DELAY)

        except Exception as e:
            logging.error("Unexpected error: %s", e)
            raise

@mcp.tool()
def move_latest_body(x : float,y:float,z:float):
    """
    Du kannst den letzten Körper in Fusion 360 verschieben in x,y und z Richtung

    """
    endpoint = config.ENDPOINTS["move_body"]
    payload = {
        "x": x,
        "y": y,
        "z": z
    }
    headers = config.HEADERS
    return send_request(endpoint, payload, headers)

@mcp.tool()
def create_thread(inside: bool, allsizes: int):
    """Erstellt ein Gewinde in Fusion 360
    Im Moment wählt der User selber in Fusioibn 360 das Profil aus
    Du musst nur angeben ob es innen oder außen sein soll
    und die länge des Gewindes
    allsizes haben folgende werte :
           # allsizes :
        #'1/4', '5/16', '3/8', '7/16', '1/2', '5/8', '3/4', '7/8', '1', '1 1/8', '1 1/4',
        # '1 3/8', '1 1/2', '1 3/4', '2', '2 1/4', '2 1/2', '2 3/4', '3', '3 1/2', '4', '4 1/2', '5')
        # allsizes = int value from 1 to 22

    """
    try:
        endpoint = config.ENDPOINTS["threaded"]
        payload = {
            "inside": inside,
            "allsizes": allsizes,

        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Create thread failed: %s", e)
        raise

@mcp.tool()
def test_connection():
    """Testes die Verbindung zum Fusion 360 Server."""
    try:
        endpoint = config.ENDPOINTS["test_connection"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("Test connection failed: %s", e)
        raise

@mcp.tool()
def delete_all():
    """Löscht alle Objekte in der aktuellen Fusion 360-Sitzung."""
    try:
        endpoint = config.ENDPOINTS["delete_everything"]
        headers = config.HEADERS
        send_request(endpoint, {}, headers)
    except Exception as e:
        logging.error("Delete failed: %s", e)
        raise

@mcp.tool()
def draw_holes(points: list, depth: float, width: float, faceindex: int = 0):
    """
    Zeichne Löcher in Fusion 360
    Übergebe die Json in richter Form
    Du muss die x und y koordinate angeben z = 0
    Das wird meistens aufgerufen wenn eine Bohrung in der Mitte eines Kreises sein soll
    Also wenn du ein zylinder baust musst du den Mittelpunkt des Zylinders angeben
    Übergebe zusätzlich die Tiefe und den Durchmesser der Bohrung
    Du machst im Moment  nur Counterbore holes
    Du brauchs den faceindex damit Fusion weiß auf welcher Fläche die Bohrung gemacht werden soll
    wenn du einen keris extrudierst ist die oberste Fläche meistens faceindex 1 untere fläche 2
    Die punkte müssen so sein, dass sie nicht außerhalb des Körpers liegen
    BSP:
    2,1mm tief = depth: 0.21
    Breite 10mm = diameter: 1.0
    {
    points : [[0,0,]],
    width : 1.0,
    depth : 0.21,
    faceindex : 0
    }
    """
    try:
        endpoint = config.ENDPOINTS["holes"]
        payload = {
            "points": points,
            "width": width,
            "depth": depth,
            "faceindex": faceindex
        }
        headers = config.HEADERS
        send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Draw holes failed: %s", e)
        raise

@mcp.tool()
def draw_witzenmannlogo(scale: float = 1.0, z: float = 1.0):
    """
    Du baust das witzenmann logo
    Du kannst es skalieren
    es ist immer im Mittelpunkt
    Du kannst die Höhe angeben mit z

    :param scale:
    :param z:
    :return:
    """
    try:
        endpoint = config.ENDPOINTS["witzenmann"]
        payload = {
            "scale": scale,
            "z": z
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Witzenmannlogo failed: %s", e)
        raise

@mcp.tool()
def spline(points: list, plane: str):
    """
    Zeichne eine Spline Kurve in Fusion 360
    Du kannst die Punkte als Liste von Listen übergeben
    Beispiel: [[0,0,0],[5,0,0],[5,5,5],[0,5,5],[0,0,0]]
    Es ist essenziell, dass du die Z-Koordinate angibst, auch wenn sie 0 ist
    Wenn nicht explizit danach gefragt ist mache es so, dass die Linien nach oben zeigen
    Du kannst die Ebene als String übergeben
    Es ist essenziell, dass die linien die gleiche ebene haben wie das profil was du sweepen willst
    """
    try:
        endpoint = config.ENDPOINTS["spline"]
        payload = {
            "points": points,
            "plane": plane
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Spline failed: %s", e)
        raise

@mcp.tool()
def sweep():
    """
    Benutzt den vorhrig erstellten spline und den davor erstellten krei,
    um eine sweep funktion auszuführen
    """
    try:
        endpoint = config.ENDPOINTS["sweep"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("Sweep failed: %s", e)
        raise

@mcp.tool()
def undo():
    """Macht die letzte Aktion rückgängig."""
    try:
        endpoint = config.ENDPOINTS["undo"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("Undo failed: %s", e)
        raise

@mcp.tool()
def count():
    """Zählt die Parameter im aktuellen Modell."""
    try:
        endpoint = config.ENDPOINTS["count_parameters"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("Count failed: %s", e)
        raise

@mcp.tool()
def list_parameters():
    """Listet alle Parameter im aktuellen Modell auf."""
    try:
        endpoint = config.ENDPOINTS["list_parameters"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("List parameters failed: %s", e)
        raise

@mcp.tool()
def export_step(name : str):
    """Exportiert das Modell als STEP-Datei."""
    try:
        endpoint = config.ENDPOINTS["export_step"]
        data = {
            "name": name
        }
        return send_request(endpoint, data, {})
    except Exception as e:
        logging.error("Export STEP failed: %s", e)
        raise

@mcp.tool()
def export_stl(name : str):
    """Exportiert das Modell als STL-Datei."""
    try:
        endpoint = config.ENDPOINTS["export_stl"]
        data = {
            "name": name
        }
        return send_request(endpoint, data, {})
    except Exception as e:
        logging.error("Export STL failed: %s", e)
        raise

@mcp.tool()
def fillet_edges(radius: float, edges: list = None):
    """Erstellt eine Abrundung an den angegebenen Kanten.

    :param radius: Fillet radius in cm
    :param edges: Optional list of edge indices to fillet. If None, attempts all edges.

    For edge-selective filleting (recommended for props):
    - Specify edge indices as a list, e.g., edges=[0, 1, 5, 8]
    - This allows sharp vertical seams while softening specific edges
    - Returns detailed confirmation with success count
    """
    try:
        endpoint = config.ENDPOINTS["fillet_edges"]
        payload = {
            "radius": radius,
            "edges": edges
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Fillet edges failed: %s", e)
        raise

@mcp.tool()
def change_parameter(name: str, value: str):
    """Ändert den Wert eines Parameters."""
    try:
        endpoint = config.ENDPOINTS["change_parameter"]
        payload = {
            "name": name,
            "value": value
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Change parameter failed: %s", e)
        raise

@mcp.tool()
def draw_cylinder(radius: float , height: float , x: float, y: float, z: float , plane: str="XY"):
    """
    Zeichne einen Zylinder, du kannst du in der XY Ebende arbeiten
    Es gibt Standartwerte
    """

    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["draw_cylinder"]
        data = {
            "radius": radius,
            "height": height,
            "x": x,
            "y": y,
            "z": z,
            "plane": plane
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Draw cylinder failed: %s", e)
        return None
@mcp.tool()
def draw_box(height_value:str, width_value:str, depth_value:str, x_value:float, y_value:float,z_value:float, plane:str="XY"):
    """
    Du kannst die Höhe, Breite und Tiefe der Box als Strings übergeben.
    Depth ist die Tiefe in z Richtung also wenn gesagt wird die Box soll flach sein,
    dann gibst du einen geringen Wert an!
    Du kannst die Koordinaten x, y,z der Box als Strings übergeben.Gib immer Koordinaten an,
    jene geben den Mittelpunkt der Box an.
    Depth ist die Tiefe in z Richtung
    Ganz wichtg 10 ist 100mm in Fusion 360
    Du kannst die Ebene als String übergeben
    Depth ist die eigentliche höhe in z Richtung
    Ein in der Luft schwebende Box machst du so:
    {
    `plane`: `XY`,
    `x_value`: 5,
    `y_value`: 5,
    `z_value`: 20,
    `depth_value`: `2`,
    `width_value`: `5`,
    `height_value`: `3`
    }
    Das kannst du beliebig anpassen

    Beispiel: "XY", "YZ", "XZ"

    """
    try:
        endpoint = config.ENDPOINTS["draw_box"]
        headers = config.HEADERS

        data = {
            "height":height_value,
            "width": width_value,
            "depth": depth_value,
            "x" : x_value,
            "y" : y_value,
            "z" : z_value,
            "Plane": plane

        }

        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Draw box failed: %s", e)
        return None

@mcp.tool()
def shell_body(thickness: float, faceindex: int):
    """
    Du kannst die Dicke der Wand als Float übergeben
    Du kannst den Faceindex als Integer übergeben
    WEnn du davor eine Box abgerundet hast muss die im klaren sein, dass du 20 neue Flächen hast.
    Die sind alle die kleinen abgerundeten
    Falls du eine Box davor die Ecken verrundet hast,
    dann ist der Facinedex der großen Flächen mindestens 21
    Es kann immer nur der letzte Body geschält werde

    :param thickness:
    :param faceindex:
    :return:
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["shell_body"]
        data = {
            "thickness": thickness,
            "faceindex": faceindex
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Shell body failed: %s", e)


@mcp.tool()
def draw_sphere(x: float, y: float, z: float, radius: float):
    """
    Zeichne eine Kugel in Fusion 360
    Du kannst die Koordinaten als Float übergeben
    Du kannst den Radius als Float übergeben
    Beispiel: "XY", "YZ", "XZ"
    Gib immer JSON SO:
    {
        "x":0,
        "y":0,
        "z":0,
        "radius":5
    }
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["draw_sphere"]
        data = {
            "x": x,
            "y": y,
            "z": z,
            "radius": radius
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Draw sphere failed: %s", e)
        raise


@mcp.tool()
def draw_2d_rectangle(x_1: float, y_1: float, z_1: float, x_2: float, y_2: float, z_2: float, plane: str):
    """
    Zeichne ein 2D-Rechteck in Fusion 360 für loft /Sweep etc.
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["draw_2d_rectangle"]
        data = {
            "x_1": x_1,
            "y_1": y_1,
            "z_1": z_1,
            "x_2": x_2,
            "y_2": y_2,
            "z_2": z_2,
            "plane": plane
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Draw 2D rectangle failed: %s", e)
        raise

@mcp.tool()
def boolean_operation(operation: str):
    """
    Führe eine boolesche Operation auf dem letzten Körper aus.
    Du kannst die Operation als String übergeben.
    Mögliche Werte sind: "cut", "join", "intersect"
    Wichtig ist, dass du vorher zwei Körper erstellt hast.

    For segmented body support:
    - "join" combines multiple bodies into one (use for boolean_join)
    - "cut" subtracts one body from another
    - "intersect" keeps only the overlapping volume

    Use list_bodies() to verify bodies before boolean operations.
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["boolean_operation"]
        data = {
            "operation": operation
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Boolean operation failed: %s", e)
        raise



@mcp.tool()
def draw_lines(points : list, plane : str):
    """
    Zeichne Linien in Fusion 360
    Du kannst die Punkte als Liste von Listen übergeben
    Beispiel: [[0,0,0],[5,0,0],[5,5,5],[0,5,5],[0,0,0]]
    Es ist essenziell, dass du die Z-Koordinate angibst, auch wenn sie 0 ist
    Wenn nicht explizit danach gefragt ist mache es so, dass die Linien nach oben zeigen
    Du kannst die Ebene als String übergeben
    Beispiel: "XY", "YZ", "XZ"
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["draw_lines"]
        data = {
            "points": points,
            "plane": plane
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Draw lines failed: %s", e)

@mcp.tool()
def extrude(value: float, angle: float = 0.0):
    """Extrudiert die letzte Skizze um einen angegebenen Wert.
    Du kannst auch einen Winkel angeben
    Returns body_id for tracking the created body.

    """
    try:
        url = config.ENDPOINTS["extrude"]
        data = {
            "value": value,
            "taperangle": angle
        }
        data = json.dumps(data)
        response = requests.post(url, data, headers=config.HEADERS)
        return response.json()
    except requests.RequestException as e:
        logging.error("Extrude failed: %s", e)
        raise


@mcp.tool()
def draw_text(text: str, plane: str, x_1: float, y_1: float, z_1: float, x_2: float, y_2: float, z_2: float, thickness: float,value: float):
    """
    Zeichne einen Text in Fusion 360 der ist ein Sketch also kannst dz  ann extruden
    Mit value kannst du angeben wie weit du den text extrudieren willst
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["draw_text"]
        data = {
            "text": text,
            "plane": plane,
            "x_1": x_1,
            "y_1": y_1,
            "z_1": z_1,
            "x_2": x_2,
            "y_2": y_2,
            "z_2": z_2,
            "thickness": thickness,
            "extrusion_value": value
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Draw text failed: %s", e)
        raise

@mcp.tool()
def extrude_thin(thickness :float, distance : float):
    """
    Du kannst die Dicke der Wand als Float übergeben
    Du kannst schöne Hohlkörper damit erstellen
    :param thickness: Die Dicke der Wand in mm
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["extrude_thin"]
        data = {
            "thickness": thickness,
            "distance": distance
        }
        return send_request(endpoint, data, headers)
    except requests.RequestException as e:
        logging.error("Extrude thin failed: %s", e)
        raise

@mcp.tool()
def cut_extrude(depth :float):
    """
    Du kannst die Tiefe des Schnitts als Float übergeben
    :param depth: Die Tiefe des Schnitts in mm
    depth muss negativ sein ganz wichtig!
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["cut_extrude"]
        data = {
            "depth": depth
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Cut extrude failed: %s", e)
        raise

@mcp.tool()
def revolve(angle : float):
    """
    Sobald du dieses tool aufrufst wird der nutzer gebeten in Fusion ein profil
    auszuwählen und dann eine Achse.
    Wir übergeben den Winkel als Float
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["revolve"]
        data = {
            "angle": angle

        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Revolve failed: %s", e)
        raise
@mcp.tool()
def draw_arc(point1 : list, point2 : list, point3 : list, plane : str):
    """
    Zeichne einen Bogen in Fusion 360
    Du kannst die Punkte als Liste von Listen übergeben
    Beispiel: point1 = [0,0,0], point2 = [5,5,5], point3 = [10,0,0]
    Du kannst die Ebene als String übergeben
    Es wird eine Linie von point1 zu point3 gezeichnet die durch point2 geht also musst du nicht extra eine Linie zeichnen
    Beispiel: "XY", "YZ", "XZ"
    """
    try:
        endpoint = config.ENDPOINTS["arc"]
        headers = config.HEADERS
        data = {
            "point1": point1,
            "point2": point2,
            "point3": point3,
            "plane": plane
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Draw arc failed: %s", e)
        raise

@mcp.tool()
def draw_one_line(x1: float, y1: float, z1: float, x2: float, y2: float, z2: float, plane: str="XY"):
    """
    Zeichne eine Linie in Fusion 360
    Du kannst die Koordinaten als Float übergeben
    Beispiel: x1 = 0.0, y1 = 0.0, z1 = 0.0, x2 = 10.0, y2 = 10.0, z2 = 10.0
    Du kannst die Ebene als String übergeben
    Beispiel: "XY", "YZ", "XZ"
    """
    try:
        endpoint = config.ENDPOINTS["draw_one_line"]
        headers = config.HEADERS
        data = {
            "x1": x1,
            "y1": y1,
            "z1": z1,
            "x2": x2,
            "y2": y2,
            "z2": z2,
            "plane": plane
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Draw one line failed: %s", e)
        raise

@mcp.tool()
def rectangular_pattern(plane: str, quantity_one: float, quantity_two: float, distance_one: float, distance_two: float, axis_one: str, axis_two: str):
    """
    Du kannst ein Rectangular Pattern (Rechteckmuster) erstellen um Objekte in einer rechteckigen Anordnung zu verteilen.
    Du musst zwei Mengen (quantity_one, quantity_two) als Float übergeben,
    zwei Abstände (distance_one, distance_two) als Float übergeben,
    Die beiden Richtungen sind die axen ( axis_one, axis_two) als String ("X", "Y" oder "Z") und die Ebene als String ("XY", "YZ" oder "XZ").
    Aus Gründen musst du distance immer mit einer 10 multiplizieren damit es in Fusion 360 stimmt.
    """
    try:

        headers = config.HEADERS
        endpoint = config.ENDPOINTS["rectangular_pattern"]
        data = {
            "plane": plane,
            "quantity_one": quantity_one,
            "quantity_two": quantity_two,
            "distance_one": distance_one,
            "distance_two": distance_two,
            "axis_one": axis_one,
            "axis_two": axis_two
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Rectangular pattern failed: %s", e)
        raise


@mcp.tool()
def circular_pattern(plane: str, quantity: float, axis: str):
    """
    Du kannst ein Circular Pattern (Kreismuster) erstellen um Objekte kreisförmig um eine Achse zu verteilen.
    Du übergibst die Anzahl der Kopien als Float, die Achse als String ("X", "Y" oder "Z") und die Ebene als String ("XY", "YZ" oder "XZ").

    Die Achse gibt an, um welche Achse rotiert wird.
    Die Ebene gibt an, in welcher Ebene das Muster verteilt wird.

    Beispiel:
    - quantity: 6.0 erstellt 6 Kopien gleichmäßig um 360° verteilt
    - axis: "Z" rotiert um die Z-Achse
    - plane: "XY" verteilt die Objekte in der XY-Ebene

    Das Feature wird auf das zuletzt erstellte/ausgewählte Objekt angewendet.
    Typische Anwendungen: Schraubenlöcher in Kreisform, Zahnrad-Zähne, Lüftungsgitter, dekorative Muster.

    Returns detailed confirmation:
    {
      "applied": true,
      "instance_count": 6,
      "pattern_id": "pattern_123",
      "axis": "Z",
      "total_angle": 360
    }
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["circular_pattern"]
        data = {
            "plane": plane,
            "quantity": quantity,
            "axis": axis
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Circular pattern failed: %s", e)
        raise

@mcp.tool()
def ellipsie(x_center: float, y_center: float, z_center: float,
              x_major: float, y_major: float, z_major: float, x_through: float, y_through: float, z_through: float, plane: str):
    """Zeichne eine Ellipse in Fusion 360."""
    try:
        endpoint = config.ENDPOINTS["ellipsie"]
        headers = config.HEADERS
        data = {
            "x_center": x_center,
            "y_center": y_center,
            "z_center": z_center,
            "x_major": x_major,
            "y_major": y_major,
            "z_major": z_major,
            "x_through": x_through,
            "y_through": y_through,
            "z_through": z_through,
            "plane": plane
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Draw ellipse failed: %s", e)
        raise

@mcp.tool()
def draw2Dcircle(radius: float, x: float, y: float, z: float, plane: str = "XY"):
    """
    Zeichne einen Kreis in Fusion 360
    Du kannst den Radius als Float übergeben
    Du kannst die Koordinaten als Float übergeben
    Du kannst die Ebene als String übergeben
    Beispiel: "XY", "YZ", "XZ"

    KRITISCH - Welche Koordinate für "nach oben":
    - XY-Ebene: z erhöhen = nach oben
    - YZ-Ebene: x erhöhen = nach oben
    - XZ-Ebene: y erhöhen = nach oben

    Gib immer JSON SO:
    {
        "radius":5,
        "x":0,
        "y":0,
        "z":0,
        "plane":"XY"
    }
    """
    try:
        headers = config.HEADERS
        endpoint = config.ENDPOINTS["draw2Dcircle"]
        data = {
            "radius": radius,
            "x": x,
            "y": y,
            "z": z,
            "plane": plane
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Draw 2D circle failed: %s", e)
        raise

@mcp.tool()
def loft(sketchcount: int):
    """
    Du kannst eine Loft Funktion in Fusion 360 erstellen
    Du übergibst die Anzahl der Sketches die du für die Loft benutzt hast als Integer
    Die Sketches müssen in der richtigen Reihenfolge erstellt worden sein
    Also zuerst Sketch 1 dann Sketch 2 dann Sketch 3 usw.
    """
    try:
        endpoint = config.ENDPOINTS["loft"]
        headers = config.HEADERS
        data = {
            "sketchcount": sketchcount
        }
        return send_request(endpoint, data, headers)

    except requests.RequestException as e:
        logging.error("Loft failed: %s", e)
        raise


@mcp.tool()
def pocket_recess(depth: float, face_index: int = None, body_id = None, sketch_id = None):
    """
    Creates a pocket/recess in an existing body by cutting a sketch.
    Now supports explicit body_id and sketch_id for precise targeting.
    This is a critical tool for creating depressions, recesses, and pockets in bodies.

    :param depth: The depth of the pocket/recess (in cm, 1 unit = 1 cm = 10mm)
    :param face_index: Optional face index (legacy parameter)
    :param body_id: Optional body ID, index, or name to cut into (for explicit targeting)
    :param sketch_id: Optional sketch ID or index to use for cutting (for explicit targeting)

    Example:
    - To create a 5mm deep pocket: depth = 0.5
    - First draw a 2D sketch (circle, rectangle, polygon), then call this tool
    - For explicit targeting: pocket_recess(depth=0.5, body_id=0, sketch_id=2)
    """
    try:
        endpoint = config.ENDPOINTS["pocket_recess"]
        payload = {
            "depth": depth,
            "face_index": face_index,
            "body_id": body_id,
            "sketch_id": sketch_id
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Pocket recess failed: %s", e)
        raise


@mcp.tool()
def sketch_on_face(body_index: int = -1, face_index: int = 0):
    """
    Creates a new sketch directly on a face of an existing body.
    This is critical for sketching on angled or curved surfaces.

    :param body_index: Index of the body (-1 for last body, 0 for first body, etc.)
    :param face_index: Index of the face to sketch on (0 for first face, 1 for second, etc.)

    Important: After creating this sketch, you can draw shapes on it, then extrude or cut.
    Face indices:
    - For a box: face 0-5 are the six faces
    - For a cylinder: face 0 is top, face 1 is bottom, face 2 is the curved side
    """
    try:
        endpoint = config.ENDPOINTS["sketch_on_face"]
        payload = {
            "body_index": body_index,
            "face_index": face_index
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Sketch on face failed: %s", e)
        raise


@mcp.tool()
def create_work_plane(plane_type: str, offset_distance: float, reference_index: int = 0):
    """
    Creates a construction/work plane for advanced sketching.
    This allows you to create reference planes offset from existing geometry.

    :param plane_type: Type of plane ('offset_xy', 'offset_xz', 'offset_yz', 'face_offset')
    :param offset_distance: Distance to offset the plane (in cm)
    :param reference_index: Face index for 'face_offset' type

    Examples:
    - Create a plane 5cm above XY: plane_type='offset_xy', offset_distance=5.0
    - Create a plane offset from a face: plane_type='face_offset', offset_distance=2.0, reference_index=0
    """
    try:
        endpoint = config.ENDPOINTS["create_work_plane"]
        payload = {
            "plane_type": plane_type,
            "offset_distance": offset_distance,
            "reference_index": reference_index
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Create work plane failed: %s", e)
        raise


@mcp.tool()
def project_edges(body_index: int = None):
    """
    Projects edges from a body onto the current sketch plane.
    This allows you to reference existing geometry in your sketch.

    :param body_index: Index of body to project from (None for last body)

    Important: Create a sketch first (like sketch_on_face or on a plane),
    then call this to project edges for reference.
    """
    try:
        endpoint = config.ENDPOINTS["project_edges"]
        payload = {
            "body_index": body_index
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Project edges failed: %s", e)
        raise


@mcp.tool()
def draw_polygon(sides: int, radius: float, x: float, y: float, z: float, plane: str = "XY"):
    """
    Draws a regular polygon with the specified number of sides.
    Perfect for creating hexagons (6 sides), pentagons (5 sides), octagons (8 sides), etc.

    :param sides: Number of sides (3 for triangle, 6 for hexagon, 8 for octagon, etc.)
    :param radius: Radius of the circumscribed circle (in cm)
    :param x: X coordinate of center
    :param y: Y coordinate of center
    :param z: Z coordinate of center
    :param plane: Plane to draw on ("XY", "XZ", "YZ")

    Example for a hexagon:
    - sides=6, radius=5.0 creates a hexagon with 5cm radius
    """
    try:
        endpoint = config.ENDPOINTS["draw_polygon"]
        payload = {
            "sides": sides,
            "radius": radius,
            "x": x,
            "y": y,
            "z": z,
            "plane": plane
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Draw polygon failed: %s", e)
        raise


@mcp.tool()
def offset_surface(distance: float, face_index: int = 0):
    """
    Creates an offset surface by offsetting faces of a body.
    Useful for creating parallel surfaces and wall thicknesses.

    :param distance: Offset distance (positive or negative, in cm)
    :param face_index: Index of the face to offset

    Example: distance=1.0 offsets the face by 1cm outward
    """
    try:
        endpoint = config.ENDPOINTS["offset_surface"]
        payload = {
            "distance": distance,
            "face_index": face_index
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Offset surface failed: %s", e)
        raise


@mcp.tool()
def mirror_feature(mirror_plane: str, body_index: int = None):
    """
    Mirrors a body across a plane for creating symmetric features.

    :param mirror_plane: Plane to mirror across ("XY", "XZ", "YZ")
    :param body_index: Index of body to mirror (None for last body)

    Example: mirror_plane="XY" mirrors the body across the XY plane
    This is useful for creating symmetric panels and features.
    """
    try:
        endpoint = config.ENDPOINTS["mirror_feature"]
        payload = {
            "mirror_plane": mirror_plane,
            "body_index": body_index
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Mirror feature failed: %s", e)
        raise


@mcp.tool()
def list_bodies():
    """
    Lists all bodies in the current design with their IDs, names, and properties.
    Essential for tracking multiple bodies in segmented prop modeling.

    Returns:
    {
      "success": true,
      "count": 4,
      "bodies": [
        {"index": 0, "name": "Body1", "body_id": "...", "volume": 100.5, "is_visible": true},
        ...
      ]
    }
    """
    try:
        endpoint = config.ENDPOINTS["list_bodies"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("List bodies failed: %s", e)
        raise


@mcp.tool()
def get_active_body():
    """
    Gets the currently active or last created body.
    Returns body_id, body_name, and index.
    """
    try:
        endpoint = config.ENDPOINTS["get_active_body"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("Get active body failed: %s", e)
        raise


@mcp.tool()
def rename_body(body_id, new_name: str):
    """
    Renames a body for better organization in complex models.

    :param body_id: Body ID (string), index (int), or current name
    :param new_name: New name for the body (e.g., "HexColumn", "ZigzagFrame", "TopLid")

    Essential for tracking components like:
    - HexColumn
    - ZigzagFrame
    - TopLid
    - BasePlatform
    """
    try:
        endpoint = config.ENDPOINTS["rename_body"]
        payload = {
            "body_id": body_id,
            "new_name": new_name
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Rename body failed: %s", e)
        raise


@mcp.tool()
def list_sketches():
    """
    Lists all sketches in the current design with their IDs, names, and properties.
    Useful for managing multiple sketches in complex modeling workflows.

    Returns:
    {
      "success": true,
      "count": 5,
      "sketches": [
        {"index": 0, "name": "Sketch1", "sketch_id": "...", "is_visible": true, "profile_count": 1},
        ...
      ]
    }
    """
    try:
        endpoint = config.ENDPOINTS["list_sketches"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("List sketches failed: %s", e)
        raise


@mcp.tool()
def get_active_sketch():
    """
    Gets the currently active or last created sketch.
    Returns sketch_id, sketch_name, index, and profile_count.
    """
    try:
        endpoint = config.ENDPOINTS["get_active_sketch"]
        return send_request(endpoint, {}, {})
    except Exception as e:
        logging.error("Get active sketch failed: %s", e)
        raise


@mcp.tool()
def activate_sketch(sketch_id):
    """
    Activates a sketch for editing by its ID or index.
    Validates the sketch exists and makes it visible if needed.

    :param sketch_id: Sketch ID or index to activate
    """
    try:
        endpoint = config.ENDPOINTS["activate_sketch"]
        payload = {
            "sketch_id": sketch_id
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Activate sketch failed: %s", e)
        raise


@mcp.tool()
def close_sketch(sketch_id = None):
    """
    Closes/deactivates a sketch.
    If sketch_id is None, closes the currently active sketch.

    :param sketch_id: Optional sketch ID or index to close

    Note: All extrude and pocket operations should be called with sketches closed.
    """
    try:
        endpoint = config.ENDPOINTS["close_sketch"]
        payload = {
            "sketch_id": sketch_id
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("Close sketch failed: %s", e)
        raise



@mcp.prompt()
def weingals():
    return """
    SCHRITT 1: Zeichne Linien
    - Benutze Tool: draw_lines
    - Ebene: XY
    - Punkte: [[0, 0], [0, -8], [1.5, -8], [1.5, -7], [0.3, -7], [0.3, -2], [3, -0.5], [3, 0], [0, 0]]

    SCHRITT 2: Drehe das Profil
    - Benutze Tool: revolve
    - Winkel: 360
    - Der Nutzer wählt in Fusion das Profil und die Achse aus
    """


@mcp.prompt()
def magnet():
    return """
    SCHRITT 1: Großer Zylinder oben
    - Benutze Tool: draw_cylinder
    - Radius: 1.59
    - Höhe: 0.3
    - Position: x=0, y=0, z=0.18
    - Ebene: XY

    SCHRITT 2: Kleiner Zylinder unten
    - Benutze Tool: draw_cylinder
    - Radius: 1.415
    - Höhe: 0.18
    - Position: x=0, y=0, z=0
    - Ebene: XY

    SCHRITT 3: Loch in die Mitte bohren
    - Benutze Tool: draw_holes
    - Punkte: [[0, 0]]
    - Durchmesser (width): 1.0
    - Tiefe (depth): 0.21
    - faceindex: 2

    SCHRITT 4: Logo drauf setzen
    - Benutze Tool: draw_witzenmannlogo
    - Skalierung (scale): 0.1
    - Höhe (z): 0.28
    """


@mcp.prompt()
def dna():
    return """
    Benutze nur die tools : draw2Dcircle , spline , sweep
    Erstelle eine DNA Doppelhelix in Fusion 360

    DNA STRANG 1:

    SCHRITT 1:
    - Benutze Tool: draw2Dcircle
    - Radius: 0.5
    - Position: x=3, y=0, z=0
    - Ebene: XY

    SCHRITT 2:
    - Benutze Tool: spline
    - Ebene: XY
    - Punkte: [[3,0,0], [2.121,2.121,6.25], [0,3,12.5], [-2.121,2.121,18.75], [-3,0,25], [-2.121,-2.121,31.25], [0,-3,37.5], [2.121,-2.121,43.75], [3,0,50]]

    SCHRITT 3: Kreis an der Linie entlang ziehen
    - Benutze Tool: sweep


    DNA STRANG 2:

    SCHRITT 4:
    - Benutze Tool: draw2Dcircle
    - Radius: 0.5
    - Position: x=-3, y=0, z=0
    - Ebene: XY

    SCHRITT 5:
    - Benutze Tool: spline
    - Ebene: XY
    - Punkte: [[-3,0,0], [-2.121,-2.121,6.25], [0,-3,12.5], [2.121,-2.121,18.75], [3,0,25], [2.121,2.121,31.25], [0,3,37.5], [-2.121,2.121,43.75], [-3,0,50]]

    SCHRITT 6: Zweiten Kreis an der zweiten Linie entlang ziehen
    - Benutze Tool: sweep

    FERTIG: Jetzt hast du eine DNA Doppelhelix!
    """


@mcp.prompt()
def flansch():
    return """
    SCHRITT 1:
    - Benutze Tool: draw_cylinder
    - Denk dir sinnvolle Maße aus (z.B. Radius: 5, Höhe: 1)
    - Position: x=0, y=0, z=0
    - Ebene: XY

    SCHRITT 2: Ln
    - Benutze Tool: draw_holes
    - Mache 6-8 Löcher im Kreis verteilt
    - Tiefe: Mehr als die Zylinderhöhe (damit sie durchgehen)
    - faceindex: 1
    - Beispiel Punkte für 6 Löcher: [[4,0], [2,3.46], [-2,3.46], [-4,0], [-2,-3.46], [2,-3.46]]

    SCHRITT 3: Frage den Nutzer
    - "Soll in der Mitte auch ein Loch sein?"

    WENN JA:
    SCHRITT 4:
    - Benutze Tool: draw2Dcircle
    - Radius: 2 (oder was der Nutzer will)
    - Position: x=0, y=0, z=0
    - Ebene: XY

    SCHRITT 5:
    - Benutze Tool: cut_extrude
    - Tiefe: +2 (pos Wert! Größer als Zylinderhöhe)
    """


@mcp.prompt()
def vase():
    return """
    SCHRITT 1:
    - Benutze Tool: draw2Dcircle
    - Radius: 2.5
    - Position: x=0, y=0, z=0
    - Ebene: XY

    SCHRITT 2:
    - Benutze Tool: draw2Dcircle
    - Radius: 1.5
    - Position: x=0, y=0, z=4
    - Ebene: XY

    SCHRITT 3:
    - Benutze Tool: draw2Dcircle
    - Radius: 3
    - Position: x=0, y=0, z=8
    - Ebene: XY

    SCHRITT 4:
    - Benutze Tool: draw2Dcircle
    - Radius: 2
    - Position: x=0, y=0, z=12
    - Ebene: XY

    SCHRITT 5:
    - Benutze Tool: loft
    - sketchcount: 4

    SCHRITT 6: Vase aushöhlen (nur Wände übrig lassen)
    - Benutze Tool: shell_body
    - Wandstärke (thickness): 0.3
    - faceindex: 1

    FERTIG: Jetzt hast du eine schöne Designer-Vase!
    """


@mcp.prompt()
def teil():
    return """
    SCHRITT 1:
    - Benutze Tool: draw_box
    - Breite (width_value): "10"
    - Höhe (height_value): "10"
    - Tiefe (depth_value): "0.5"
    - Position: x=0, y=0, z=0
    - Ebene: XY

    SCHRITT 2: Kleine Löcher bohren
    - Benutze Tool: draw_holes
    - 8 Löcher total: 4 in den Ecken + 4 näher zur Mitte
    - Beispiel Punkte: [[4,4], [4,-4], [-4,4], [-4,-4], [2,2], [2,-2], [-2,2], [-2,-2]]
    - Durchmesser (width): 0.5
    - Tiefe (depth): 0.2
    - faceindex: 4

    SCHRITT 3: Kreis in der Mitte zeichnen
    - Benutze Tool: draw2Dcircle
    - Radius: 1
    - Position: x=0, y=0, z=0
    - Ebene: XY

    SCHRITT 4:
    - Benutze Tool: cut_extrude
    - Tiefe: +10 (MUSS Positiv SEIN!)

    SCHRITT 5: Sage dem Nutzer
    - "Bitte wähle jetzt in Fusion 360 die innere Fläche des mittleren Lochs aus"

    SCHRITT 6: Gewinde erstellen
    - Benutze Tool: create_thread
    - inside: True (Innengewinde)
    - allsizes: 10 (für 1/4 Zoll Gewinde)

    FERTIG: Teil mit Löchern und Gewinde ist fertig!
    """


@mcp.prompt()
def kompensator():
    prompt = """
                Bau einen Kompensator in Fusion 360 mit dem MCP: Lösche zuerst alles.
                Erstelle dann ein dünnwandiges Rohr: Zeichne einen 2D-Kreis mit Radius 5 in der XY-Ebene bei z=0,
                extrudiere ihn thin mit distance 10 und thickness 0.1. Füge dann 8 Ringe nacheinander übereinander hinzu (Erst Kreis dann Extrusion 8 mal): Für jeden Ring in
                den Höhen z=1 bis z=8 zeichne einen 2D-Kreis mit Radius 5.1 in der XY-Ebene und extrudiere ihn thin mit distance 0.5 und thickness 0.5.
                Verwende keine boolean operations, lass die Ringe als separate Körper. Runde anschließend die Kanten mit Radius 0.2 ab.
                Mache schnell!!!!!!

                """
    return prompt


#########################################################################################
### NEW ENHANCED TOOLS - Phase 1-4 (MCP Tool Definitions) ###
#########################################################################################

@mcp.tool()
def get_sketch_status(sketch_id: str = None, include_geometry: bool = True):
    """
    Validate sketch state and content before closing it.

    **CRITICAL**: Use this to verify geometry was actually accepted before proceeding.
    Returns profile count, segment count, and validity status.

    :param sketch_id: Sketch ID or index (None = current sketch)
    :param include_geometry: Include detailed geometry analysis
    :return: Validation result with profile count and geometry status

    **Usage Example:**
    ```python
    # Draw geometry
    draw_lines(points=[...])

    # VERIFY before closing
    status = get_sketch_status()
    if not status["geometry_valid"]:
        print(f"ERROR: {status['error_message']}")
        return

    if status["profile_count"] != 5:
        print("Expected 5 rectangles")
        return

    close_sketch()  # Now safe to close
    ```
    """
    try:
        endpoint = config.ENDPOINTS["get_sketch_status"]
        payload = {
            "sketch_id": sketch_id,
            "include_geometry": include_geometry
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("get_sketch_status failed: %s", e)
        raise


@mcp.tool()
def list_faces(body_id):
    """
    Query all faces of a body with geometric properties (not just indices).

    **WHY NEEDED**: Face indices change after boolean operations. This provides semantic understanding.

    Returns face type, area, normal vector, position, orientation (front/back/top/bottom), and adjacent faces.

    :param body_id: Body ID, index, or name
    :return: List of all faces with properties

    **Usage Example:**
    ```python
    # Instead of hardcoding face_index=1
    faces = list_faces(body_id=1)

    # Find front face (normal pointing in +Y direction)
    front_face = next(f for f in faces["faces"] if f["normal"] == [0, 1, 0])
    sketch_on_face(body_id=1, face_index=front_face["index"])
    ```
    """
    try:
        endpoint = config.ENDPOINTS["list_faces"]
        payload = {"body_id": body_id}
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("list_faces failed: %s", e)
        raise


@mcp.tool()
def pocket_recess_safe(body_id, sketch_id, depth: float, operation: str = "cut",
                       validate_before: bool = True, validate_after: bool = True):
    """
    Create pocket with complete validation and result confirmation.

    **CRITICAL**: Returns success=true/false with actual volume changes. No more silent failures!

    :param body_id: Body ID, index, or name to cut into
    :param sketch_id: Sketch ID or index to use for cutting
    :param depth: Depth of pocket in cm (1 unit = 1 cm = 10mm)
    :param operation: "cut", "join", or "intersect"
    :param validate_before: Validate sketch has profiles before cutting
    :param validate_after: Verify volume actually changed
    :return: Detailed result with volume changes and validation status

    **Usage Example:**
    ```python
    # Create pocket with guaranteed validation
    result = pocket_recess_safe(
        body_id=1,
        sketch_id=5,
        depth=0.5,
        validate_before=True,
        validate_after=True
    )

    # Check result before proceeding
    if not result["success"]:
        print(f"ERROR: {result['error']}")
        undo()
    else:
        print(f"Pocket applied: {result['volume_removed']} cm³ removed")
    ```
    """
    try:
        endpoint = config.ENDPOINTS["pocket_recess_safe"]
        payload = {
            "body_id": body_id,
            "sketch_id": sketch_id,
            "depth": depth,
            "operation": operation,
            "validate_before": validate_before,
            "validate_after": validate_after
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("pocket_recess_safe failed: %s", e)
        raise


@mcp.tool()
def get_feature_history(body_id, include_parameters: bool = True, include_errors: bool = True):
    """
    List all features (extrudes, pockets, fillets, etc.) applied to a body.

    **WHY NEEDED**: Verify which operations actually succeeded. Audit trail for multi-step builds.

    :param body_id: Body ID, index, or name
    :param include_parameters: Include feature parameters
    :param include_errors: Include error messages for failed features
    :return: Complete feature history with status and errors

    **Usage Example:**
    ```python
    # Build complex geometry
    extrude(value=20)
    pocket_recess(body_id=1, depth=0.5)
    pocket_recess(body_id=1, depth=0.3)  # Might fail

    # Audit what actually succeeded
    history = get_feature_history(body_id=1)

    failed_features = [f for f in history["features"] if f["status"] == "failed"]
    if failed_features:
        print(f"WARNING: {len(failed_features)} features failed")
        for f in failed_features:
            print(f"  - {f['name']}: {f['error_message']}")
    ```
    """
    try:
        endpoint = config.ENDPOINTS["get_feature_history"]
        payload = {
            "body_id": body_id,
            "include_parameters": include_parameters,
            "include_errors": include_errors
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("get_feature_history failed: %s", e)
        raise


@mcp.tool()
def find_face_by_property(body_id, selector: str = None, normal: list = None,
                         area_range: dict = None, position: dict = None,
                         return_all_matches: bool = False):
    """
    Locate face(s) by geometric criteria instead of fragile indices.

    **WHY NEEDED**: Hardcoded face_index=1 breaks after boolean operations. Semantic selection is robust.

    :param body_id: Body ID, index, or name
    :param selector: "front", "back", "top", "bottom", "left", "right", "largest", "smallest"
    :param normal: Normal vector [x, y, z] (e.g., [0, 1, 0] for front face)
    :param area_range: {"min": float, "max": float}
    :param position: {"point": [x, y, z], "tolerance": float}
    :param return_all_matches: Return all matching faces (default: first match only)
    :return: Matching face(s) with indices

    **Usage Example:**
    ```python
    # Find front face semantically (no hardcoded index)
    front = find_face_by_property(body_id=1, selector="front")
    front_face_index = front["primary_face_index"]

    # Create sketch on front face (works even after topology changes)
    sketch_on_face(body_id=1, face_index=front_face_index)
    ```
    """
    try:
        endpoint = config.ENDPOINTS["find_face_by_property"]
        payload = {
            "body_id": body_id,
            "selector": selector,
            "normal": normal,
            "area_range": area_range,
            "position": position,
            "return_all_matches": return_all_matches
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("find_face_by_property failed: %s", e)
        raise


@mcp.tool()
def draw_rectangles_batch(plane: str, rectangles: list):
    """
    Draw multiple rectangles in a single sketch in one operation.

    **WHY NEEDED**: Sequential rectangle draws accumulate errors. Batch reduces failure points.

    :param plane: "XY", "YZ", or "XZ"
    :param rectangles: List of rectangle dicts with x_min, x_max, y_min, y_max, z_center
    :return: Sketch ID and success count

    **Usage Example:**
    ```python
    # Define all 5 vent bands at once
    vent_bands = [
        {"x_min": -10, "x_max": 10, "y_min": 3, "y_max": 4, "z_center": 4},
        {"x_min": -10, "x_max": 10, "y_min": 3, "y_max": 4, "z_center": 8},
        {"x_min": -10, "x_max": 10, "y_min": 3, "y_max": 4, "z_center": 12},
        {"x_min": -10, "x_max": 10, "y_min": 3, "y_max": 4, "z_center": 16},
        {"x_min": -10, "x_max": 10, "y_min": 3, "y_max": 4, "z_center": 20},
    ]

    sketch_on_face(body_id=1, face_index=1)
    result = draw_rectangles_batch(plane="XY", rectangles=vent_bands)
    assert result["rectangles_failed"] == 0, "Some rectangles failed"
    close_sketch()
    pocket_recess_safe(body_id=1, depth=0.5)  # Creates 5 pockets at once
    ```
    """
    try:
        endpoint = config.ENDPOINTS["draw_rectangles_batch"]
        payload = {
            "plane": plane,
            "rectangles": rectangles
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("draw_rectangles_batch failed: %s", e)
        raise


@mcp.tool()
def pocket_smart(body_id, sketch_id, depth_mode: str, depth_value: float,
                from_face: str = "sketch_plane", snap_to_geometry: bool = False,
                validate_after: bool = True):
    """
    Create pocket with intelligent depth calculation.

    **DEPTH MODES:**
    - "absolute": Cut exactly depth_value cm
    - "through": Cut all the way through (ignores depth_value)
    - "wall_thickness": Leave exactly depth_value cm of material remaining
    - "percentage": Cut depth_value% of the current thickness

    :param body_id: Body ID, index, or name
    :param sketch_id: Sketch ID or index
    :param depth_mode: "absolute", "through", "wall_thickness", or "percentage"
    :param depth_value: Depth value (interpretation depends on mode)
    :param from_face: "top", "bottom", or "sketch_plane"
    :param snap_to_geometry: Snap to internal geometry
    :param validate_after: Validate result
    :return: Result with calculated depth

    **Usage Example:**
    ```python
    # Old way: manually calculate depth
    pocket_recess_safe(body_id=1, depth=0.82)  # Must calculate manually

    # New way: specify desired wall thickness
    pocket_smart(
        body_id=1,
        sketch_id=5,
        depth_mode="wall_thickness",
        depth_value=0.3  # MCP calculates the cut depth
    )
    ```
    """
    try:
        endpoint = config.ENDPOINTS["pocket_smart"]
        payload = {
            "body_id": body_id,
            "sketch_id": sketch_id,
            "depth_mode": depth_mode,
            "depth_value": depth_value,
            "from_face": from_face,
            "snap_to_geometry": snap_to_geometry,
            "validate_after": validate_after
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("pocket_smart failed: %s", e)
        raise


@mcp.tool()
def begin_transaction(transaction_id: str, description: str = "",
                     auto_validate: bool = True, auto_rollback_on_error: bool = False):
    """
    Begin a transaction to group multiple operations with atomic commit/rollback.

    **WHY NEEDED**: One failed operation ruins entire sequence. Transactions enable safe multi-step builds.

    :param transaction_id: Unique transaction ID
    :param description: Optional description
    :param auto_validate: Auto-validate each step
    :param auto_rollback_on_error: Auto-rollback on any error
    :return: Transaction confirmation

    **Usage Example:**
    ```python
    # Start transaction
    begin_transaction("lower_vent_segment")

    # Execute sequence
    sketch_on_face(body_id="body_1", face_id="front")
    draw_rectangles_batch(plane="XY", rectangles=vent_bands)
    close_sketch()
    result = pocket_recess_safe(body_id="body_1", depth=0.5)

    # Commit or rollback
    if not result["success"]:
        rollback_transaction("lower_vent_segment")
    else:
        commit_transaction("lower_vent_segment")
    ```
    """
    try:
        endpoint = config.ENDPOINTS["begin_transaction"]
        payload = {
            "transaction_id": transaction_id,
            "description": description,
            "auto_validate": auto_validate,
            "auto_rollback_on_error": auto_rollback_on_error
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("begin_transaction failed: %s", e)
        raise


@mcp.tool()
def commit_transaction(transaction_id: str, force: bool = False):
    """
    Commit a transaction atomically.

    :param transaction_id: Transaction ID to commit
    :param force: Force commit even if validation fails
    :return: Commit result with operation summary
    """
    try:
        endpoint = config.ENDPOINTS["commit_transaction"]
        payload = {
            "transaction_id": transaction_id,
            "force": force
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("commit_transaction failed: %s", e)
        raise


@mcp.tool()
def rollback_transaction(transaction_id: str):
    """
    Rollback a transaction (undo all operations).

    :param transaction_id: Transaction ID to rollback
    :return: Rollback result
    """
    try:
        endpoint = config.ENDPOINTS["rollback_transaction"]
        payload = {"transaction_id": transaction_id}
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("rollback_transaction failed: %s", e)
        raise


@mcp.tool()
def get_operation_log(last_n_operations: int = 20, body_id = None,
                     operation_type: str = None, status_filter: str = None):
    """
    Access detailed operation history for debugging.

    **WHY NEEDED**: Silent failures are invisible. This provides complete audit trail.

    :param last_n_operations: Number of recent operations to return
    :param body_id: Filter by body ID
    :param operation_type: Filter by operation type
    :param status_filter: "success", "warning", "failed", or "all"
    :return: Operation log with timestamps and state changes

    **Usage Example:**
    ```python
    # Something went wrong
    log = get_operation_log(status_filter="failed")

    if log["operation_count"] > 0:
        print("Failed operations:")
        for op in log["operations"]:
            print(f"  {op['operation']}: {op['error_message']}")
    ```
    """
    try:
        endpoint = config.ENDPOINTS["get_operation_log"]
        payload = {
            "last_n_operations": last_n_operations,
            "body_id": body_id,
            "operation_type": operation_type,
            "status_filter": status_filter
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("get_operation_log failed: %s", e)
        raise


@mcp.tool()
def create_sketch_on_body_plane(body_id, plane: str, z_offset: float = 0, name: str = None):
    """
    Create sketch directly on XY/YZ/XZ plane without face dependency.

    :param body_id: Body ID
    :param plane: "XY", "YZ", or "XZ"
    :param z_offset: Offset from plane in cm
    :param name: Optional sketch name
    :return: Sketch ID
    """
    try:
        endpoint = config.ENDPOINTS["create_sketch_on_body_plane"]
        payload = {
            "body_id": body_id,
            "plane": plane,
            "z_offset": z_offset,
            "name": name
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("create_sketch_on_body_plane failed: %s", e)
        raise


@mcp.tool()
def validate_face_exists(body_id, face_index: int):
    """
    Check if face index is still valid after topology changes.

    **WHY NEEDED**: After pockets/booleans, face indices change. Validate before using.

    :param body_id: Body ID
    :param face_index: Face index to validate
    :return: Validation result with suggestions
    """
    try:
        endpoint = config.ENDPOINTS["validate_face_exists"]
        payload = {
            "body_id": body_id,
            "face_index": face_index
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("validate_face_exists failed: %s", e)
        raise


@mcp.tool()
def select_faces_by_semantic(body_id, selectors: list):
    """
    Batch select multiple faces using semantic names.

    :param body_id: Body ID
    :param selectors: List of selectors (e.g., ["front", "back", "top"])
    :return: Selected faces
    """
    try:
        endpoint = config.ENDPOINTS["select_faces_by_semantic"]
        payload = {
            "body_id": body_id,
            "selectors": selectors
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("select_faces_by_semantic failed: %s", e)
        raise


@mcp.tool()
def clear_sketch(sketch_id = None):
    """
    Safely clear active sketch without closing it.

    **WHY NEEDED**: If geometry fails, erase and restart without closing bad sketch.

    :param sketch_id: Sketch ID (None = current sketch)
    :return: Clear result
    """
    try:
        endpoint = config.ENDPOINTS["clear_sketch"]
        payload = {"sketch_id": sketch_id}
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("clear_sketch failed: %s", e)
        raise


@mcp.tool()
def extrude_safe(value: float, sketch_id, body_id, direction: str = "normal",
                validate_before: bool = True, validate_after: bool = True):
    """
    Extrude with full pre/post validation.

    **WHY NEEDED**: Ensure sketch is valid and extrusion succeeds.

    :param value: Extrusion distance in cm
    :param sketch_id: Sketch ID
    :param body_id: Body ID
    :param direction: "normal", "both", or "symmetric"
    :param validate_before: Validate sketch before extruding
    :param validate_after: Verify volume changed
    :return: Detailed result with volume changes
    """
    try:
        endpoint = config.ENDPOINTS["extrude_safe"]
        payload = {
            "value": value,
            "sketch_id": sketch_id,
            "body_id": body_id,
            "direction": direction,
            "validate_before": validate_before,
            "validate_after": validate_after
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("extrude_safe failed: %s", e)
        raise


#########################################################################################
### PROP PERFECTION TOOLS ###
#########################################################################################

@mcp.tool()
def chamfer_edges(distance: float, edges: list = None, angle: float = 45.0):
    """
    Create angled beveled edges (chamfers) on specified edges.
    Unlike fillets (rounded), chamfers create flat angled surfaces.

    **WHY NEEDED**: Props often have sharp beveled edges, not rounded fillets.
    Perfect for creating the angled edges on the Stargate console panels.

    :param distance: Chamfer distance in cm (how far from edge the bevel extends)
    :param edges: List of edge indices to chamfer, or None for all edges
    :param angle: Chamfer angle in degrees (default 45°)
    :return: Chamfer result with success status

    **Usage Example:**
    ```python
    # 45° chamfer on top octagonal frame
    result = chamfer_edges(distance=0.5, edges=[20, 21, 22, 23], angle=45)
    print(f"Chamfered {result['successful_chamfers']} edges")

    # Angled bevel on base edges (60° angle)
    chamfer_edges(distance=0.3, edges=[0, 1, 2, 3, 4, 5], angle=60)
    ```

    **Returns:**
    ```json
    {
      "success": true,
      "successful_chamfers": 4,
      "failed_edges": 0,
      "distance": 0.5,
      "angle": 45.0,
      "message": "Successfully chamfered 4 edge(s)"
    }
    ```

    **Best Practices:**
    - Use chamfer for sharp, angular edges (consoles, mechanical parts)
    - Use fillet for smooth, organic edges (ergonomic handles)
    - Specify edge indices for selective chamfering
    - Apply chamfers AFTER all pockets/recesses to avoid edge breakage
    """
    try:
        endpoint = config.ENDPOINTS["chamfer_edges"]
        payload = {
            "distance": distance,
            "edges": edges,
            "angle": angle
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("chamfer_edges failed: %s", e)
        raise


@mcp.tool()
def split_body(body_id = None, split_tool: str = "XY", keep_both: bool = True):
    """
    Split a body using a construction plane.
    Useful for multi-material props, assembly separation, or splitting large models for 3D printing.

    **WHY NEEDED**: Large props often need to be split for printing bed size limitations,
    or for creating multi-material assemblies (metallic frame + translucent crystal).

    :param body_id: Body ID to split (None = last body)
    :param split_tool: Plane to split with: "XY", "YZ", or "XZ"
    :param keep_both: If True, keeps both halves; if False, removes one half
    :return: Split result with body information

    **Usage Example:**
    ```python
    # Split console at mid-height for separate base/top printing
    result = split_body(body_id="HexColumn", split_tool="XY", keep_both=True)
    print(f"Split into {result['result_bodies']} bodies")

    # Name the resulting bodies
    rename_body(body_id="body_0", new_name="HexColumn_Base")
    rename_body(body_id="body_1", new_name="HexColumn_Top")

    # Split for multi-material (keep top, remove bottom)
    split_body(body_id="CrystalWindow", split_tool="XY", keep_both=False)
    ```

    **Returns:**
    ```json
    {
      "success": true,
      "original_body": "HexColumn",
      "split_plane": "XY",
      "keep_both": true,
      "result_bodies": 2,
      "message": "Body split using XY plane"
    }
    ```

    **Best Practices:**
    - Split AFTER all features are applied
    - Use list_bodies() to verify result bodies
    - Rename bodies immediately after splitting for clarity
    - For 3D printing: split to fit printer bed (e.g., 200mm x 200mm)
    """
    try:
        endpoint = config.ENDPOINTS["split_body"]
        payload = {
            "body_id": body_id,
            "split_tool": split_tool,
            "keep_both": keep_both
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("split_body failed: %s", e)
        raise


@mcp.tool()
def scale_body(body_id = None, scale_factor: float = 1.0, uniform: bool = True,
              scale_x: float = 1.0, scale_y: float = 1.0, scale_z: float = 1.0):
    """
    Scale a body by specified factors.
    Useful for adjusting prop sizes or creating scaled replicas.

    **WHY NEEDED**: Props often need size adjustments (1:1 scale → desk model),
    or non-uniform scaling for specific proportions.

    :param body_id: Body ID to scale (None = last body)
    :param scale_factor: Uniform scale factor (used if uniform=True)
    :param uniform: If True, uses scale_factor; if False, uses scale_x/y/z
    :param scale_x: X-axis scale factor (if uniform=False)
    :param scale_y: Y-axis scale factor (if uniform=False)
    :param scale_z: Z-axis scale factor (if uniform=False)
    :return: Scale result with scaling information

    **Usage Example:**
    ```python
    # Scale entire console to 80% for desk model
    result = scale_body(body_id="HexColumn", scale_factor=0.8, uniform=True)
    print(f"Scaled to {result['scale_x']}x")

    # Non-uniform scaling (stretch vertically, compress horizontally)
    scale_body(
        body_id="Pedestal",
        uniform=False,
        scale_x=0.5,
        scale_y=0.5,
        scale_z=1.5
    )

    # Create miniature replica (25% scale)
    scale_body(body_id="Console_Assembly", scale_factor=0.25)
    ```

    **Returns:**
    ```json
    {
      "success": true,
      "body_name": "HexColumn",
      "uniform": true,
      "scale_x": 0.8,
      "scale_y": 0.8,
      "scale_z": 0.8,
      "message": "Body scaled by 0.8"
    }
    ```

    **Best Practices:**
    - Scale AFTER all features are complete
    - Use uniform scaling to maintain proportions
    - For 3D printing: scale to fit printer bed
    - For miniatures: 0.1-0.5x scale factors common
    - For display models: 0.6-0.8x often ideal
    """
    try:
        endpoint = config.ENDPOINTS["scale_body"]
        payload = {
            "body_id": body_id,
            "scale_factor": scale_factor,
            "uniform": uniform,
            "scale_x": scale_x,
            "scale_y": scale_y,
            "scale_z": scale_z
        }
        headers = config.HEADERS
        return send_request(endpoint, payload, headers)
    except Exception as e:
        logging.error("scale_body failed: %s", e)
        raise


#########################################################################################
### END OF NEW ENHANCED TOOLS ###
#########################################################################################


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server_type", type=str, default="sse", choices=["sse", "stdio"]
    )
    args = parser.parse_args()

    mcp.run(transport=args.server_type)
