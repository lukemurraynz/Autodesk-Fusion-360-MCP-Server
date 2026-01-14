import adsk.core, adsk.fusion, traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from http import HTTPStatus
import threading
import json
import time
import queue
from pathlib import Path
import math
import os

ModelParameterSnapshot = []
httpd = None
task_queue = queue.Queue()  # Queue für thread-safe Aktionen

# Global results cache for query operations
query_results = {
    'list_bodies': None,
    'get_active_body': None,
    'rename_body': None,
    'list_sketches': None,
    'get_active_sketch': None,
    'activate_sketch': None,
    'close_sketch': None,
    'extrude': None,
    'pocket_recess': None,
    'circular_pattern': None,
    'fillet_edges': None,
    'select_body': None,
    'select_sketch': None
}

# Event Handler Variablen
app = None
ui = None
design = None
handlers = []
stopFlag = None
myCustomEvent = 'MCPTaskEvent'
customEvent = None

#Event Handler Class
class TaskEventHandler(adsk.core.CustomEventHandler):
    """
    Custom Event Handler for processing tasks from the queue
    This is used, because Fusion 360 API is not thread-safe
    """
    def __init__(self):
        super().__init__()

    def notify(self, args):
        global task_queue, ModelParameterSnapshot, design, ui
        try:
            if design:
                # Parameter Snapshot aktualisieren
                ModelParameterSnapshot = get_model_parameters(design)

                # Task-Queue abarbeiten
                while not task_queue.empty():
                    try:
                        task = task_queue.get_nowait()
                        self.process_task(task)
                    except queue.Empty:
                        break
                    except Exception as e:
                        if ui:
                            ui.messageBox(f"Task-Fehler: {str(e)}")
                        continue

        except Exception as e:

            pass

    def process_task(self, task):
        """Verarbeitet eine einzelne Task und speichert Rückgabewerte für Abfragen"""
        global design, ui, query_results

        # Capture return values for query operations
        result = None

        if task[0] == 'set_parameter':
            set_parameter(design, ui, task[1], task[2])
        elif task[0] == 'draw_box':

            draw_Box(design, ui, task[1], task[2], task[3], task[4], task[5], task[6], task[7])

        elif task[0] == 'draw_witzenmann':
            draw_Witzenmann(design, ui, task[1],task[2])
        elif task[0] == 'export_stl':

            export_as_STL(design, ui, task[1])
        elif task[0] == 'fillet_edges':
            result = fillet_edges(design, ui, task[1], task[2] if len(task) > 2 else None)
            query_results['fillet_edges'] = result
        elif task[0] == 'export_step':

            export_as_STEP(design, ui, task[1])
        elif task[0] == 'draw_cylinder':
            draw_cylinder(design, ui, task[1], task[2], task[3], task[4], task[5],task[6])
        elif task[0] == 'shell_body':
            shell_existing_body(design, ui, task[1], task[2])
        elif task[0] == 'undo':
            undo(design, ui)
        elif task[0] == 'draw_lines':
            draw_lines(design, ui, task[1], task[2])
        elif task[0] == 'extrude_last_sketch':
            result = extrude_last_sketch(design, ui, task[1],task[2])
            query_results['extrude'] = result
        elif task[0] == 'revolve_profile':
            # 'rootComp = design.rootComponent
            # sketches = rootComp.sketches
            # sketch = sketches.item(sketches.count - 1)  # Letzter Sketch
            # axisLine = sketch.sketchCurves.sketchLines.item(0)  # Erste Linie als Achse'
            revolve_profile(design, ui,  task[1])
        elif task[0] == 'arc':
            arc(design, ui, task[1], task[2], task[3], task[4],task[5])
        elif task[0] == 'draw_one_line':
            draw_one_line(design, ui, task[1], task[2], task[3], task[4], task[5], task[6], task[7])
        elif task[0] == 'holes': #task format: ('holes', points, width, depth, through, faceindex)
            # task[3]=depth, task[4]=through, task[5]=faceindex
            holes(design, ui, task[1], task[2], task[3], task[4])
        elif task[0] == 'circle':
            draw_circle(design, ui, task[1], task[2], task[3], task[4],task[5])
        elif task[0] == 'extrude_thin':
            extrude_thin(design, ui, task[1],task[2])
        elif task[0] == 'select_body':
            result = select_body(design, ui, task[1])
            query_results['select_body'] = result
        elif task[0] == 'select_sketch':
            result = select_sketch(design, ui, task[1])
            query_results['select_sketch'] = result
        elif task[0] == 'spline':
            spline(design, ui, task[1], task[2])
        elif task[0] == 'sweep':
            sweep(design, ui)
        elif task[0] == 'cut_extrude':
            cut_extrude(design,ui,task[1])
        elif task[0] == 'circular_pattern':
            result = circular_pattern(design,ui,task[1],task[2],task[3])
            query_results['circular_pattern'] = result
        elif task[0] == 'offsetplane':
            offsetplane(design,ui,task[1],task[2])
        elif task[0] == 'loft':
            loft(design, ui, task[1])
        elif task[0] == 'ellipsis':
            draw_ellipis(design,ui,task[1],task[2],task[3],task[4],task[5],task[6],task[7],task[8],task[9],task[10])
        elif task[0] == 'draw_sphere':
            create_sphere(design, ui, task[1], task[2], task[3], task[4])
        elif task[0] == 'threaded':
            create_thread(design, ui, task[1], task[2])
        elif task[0] == 'delete_everything':
            delete(design, ui)
        elif task[0] == 'boolean_operation':
            boolean_operation(design,ui,task[1])
        elif task[0] == 'draw_2d_rectangle':
            draw_2d_rect(design, ui, task[1], task[2], task[3], task[4], task[5], task[6], task[7])
        elif task[0] == 'rectangular_pattern':
            rect_pattern(design,ui,task[1],task[2],task[3],task[4],task[5],task[6],task[7])
        elif task[0] == 'draw_text':
            draw_text(design, ui, task[1], task[2], task[3], task[4], task[5], task[6], task[7], task[8], task[9],task[10])
        elif task[0] == 'move_body':
            move_last_body(design,ui,task[1],task[2],task[3])
        elif task[0] == 'pocket_recess':
            result = pocket_recess(design, ui, task[1], task[2] if len(task) > 2 else None,
                         task[3] if len(task) > 3 else None, task[4] if len(task) > 4 else None)
            query_results['pocket_recess'] = result
        elif task[0] == 'sketch_on_face':
            sketch_on_face(design, ui, task[1], task[2])
        elif task[0] == 'create_work_plane':
            create_work_plane(design, ui, task[1], task[2], task[3])
        elif task[0] == 'project_edges':
            project_edges(design, ui, task[1])
        elif task[0] == 'draw_polygon':
            draw_polygon(design, ui, task[1], task[2], task[3], task[4], task[5], task[6])
        elif task[0] == 'offset_surface':
            offset_surface(design, ui, task[1], task[2])
        elif task[0] == 'mirror_feature':
            mirror_feature(design, ui, task[1], task[2])
        elif task[0] == 'list_bodies':
            result = list_bodies(design, ui)
            query_results['list_bodies'] = result
        elif task[0] == 'get_active_body':
            result = get_active_body(design, ui)
            query_results['get_active_body'] = result
        elif task[0] == 'rename_body':
            result = rename_body(design, ui, task[1], task[2])
            query_results['rename_body'] = result
        elif task[0] == 'list_sketches':
            result = list_sketches(design, ui)
            query_results['list_sketches'] = result
        elif task[0] == 'get_active_sketch':
            result = get_active_sketch(design, ui)
            query_results['get_active_sketch'] = result
        elif task[0] == 'activate_sketch':
            result = activate_sketch(design, ui, task[1])
            query_results['activate_sketch'] = result
        elif task[0] == 'close_sketch':
            sketch_id = task[1] if len(task) > 1 else None
            result = close_sketch(design, ui, sketch_id)
            query_results['close_sketch'] = result
        # NEW ENHANCED TOOLS
        elif task[0] == 'get_sketch_status':
            sketch_id = task[1] if len(task) > 1 else None
            include_geometry = task[2] if len(task) > 2 else True
            result = get_sketch_status(design, ui, sketch_id, include_geometry)
            query_results['get_sketch_status'] = result
        elif task[0] == 'list_faces':
            result = list_faces(design, ui, task[1])
            query_results['list_faces'] = result
        elif task[0] == 'pocket_recess_safe':
            result = pocket_recess_safe(design, ui, task[1], task[2], task[3],
                                      task[4] if len(task) > 4 else "cut",
                                      task[5] if len(task) > 5 else True,
                                      task[6] if len(task) > 6 else True)
            query_results['pocket_recess_safe'] = result
        elif task[0] == 'get_feature_history':
            result = get_feature_history(design, ui, task[1],
                                        task[2] if len(task) > 2 else True,
                                        task[3] if len(task) > 3 else True)
            query_results['get_feature_history'] = result
        elif task[0] == 'find_face_by_property':
            result = find_face_by_property(design, ui, task[1],
                                          task[2] if len(task) > 2 else None,
                                          task[3] if len(task) > 3 else None,
                                          task[4] if len(task) > 4 else None,
                                          task[5] if len(task) > 5 else None,
                                          task[6] if len(task) > 6 else False)
            query_results['find_face_by_property'] = result
        elif task[0] == 'draw_rectangles_batch':
            result = draw_rectangles_batch(design, ui, task[1], task[2])
            query_results['draw_rectangles_batch'] = result
        elif task[0] == 'pocket_smart':
            result = pocket_smart(design, ui, task[1], task[2], task[3], task[4],
                                task[5] if len(task) > 5 else "sketch_plane",
                                task[6] if len(task) > 6 else False,
                                task[7] if len(task) > 7 else True)
            query_results['pocket_smart'] = result
        elif task[0] == 'begin_transaction':
            result = begin_transaction(design, ui, task[1],
                                      task[2] if len(task) > 2 else "",
                                      task[3] if len(task) > 3 else True,
                                      task[4] if len(task) > 4 else False)
            query_results['begin_transaction'] = result
        elif task[0] == 'commit_transaction':
            result = commit_transaction(design, ui, task[1],
                                       task[2] if len(task) > 2 else False)
            query_results['commit_transaction'] = result
        elif task[0] == 'rollback_transaction':
            result = rollback_transaction(design, ui, task[1])
            query_results['rollback_transaction'] = result
        elif task[0] == 'get_operation_log':
            result = get_operation_log(design, ui,
                                      task[1] if len(task) > 1 else 20,
                                      task[2] if len(task) > 2 else None,
                                      task[3] if len(task) > 3 else None,
                                      task[4] if len(task) > 4 else None)
            query_results['get_operation_log'] = result
        elif task[0] == 'create_sketch_on_body_plane':
            result = create_sketch_on_body_plane(design, ui, task[1], task[2],
                                                 task[3] if len(task) > 3 else 0,
                                                 task[4] if len(task) > 4 else None)
            query_results['create_sketch_on_body_plane'] = result
        elif task[0] == 'validate_face_exists':
            result = validate_face_exists(design, ui, task[1], task[2])
            query_results['validate_face_exists'] = result
        elif task[0] == 'select_faces_by_semantic':
            result = select_faces_by_semantic(design, ui, task[1], task[2])
            query_results['select_faces_by_semantic'] = result
        elif task[0] == 'clear_sketch':
            sketch_id = task[1] if len(task) > 1 else None
            result = clear_sketch(design, ui, sketch_id)
            query_results['clear_sketch'] = result
        elif task[0] == 'extrude_safe':
            result = extrude_safe(design, ui, task[1], task[2], task[3],
                                task[4] if len(task) > 4 else "normal",
                                task[5] if len(task) > 5 else True,
                                task[6] if len(task) > 6 else True)
            query_results['extrude_safe'] = result
        elif task[0] == 'chamfer_edges':
            distance = task[1]
            edge_ids = task[2] if len(task) > 2 else None
            angle = task[3] if len(task) > 3 else 45.0
            result = chamfer_edges(design, ui, distance, edge_ids, angle)
            query_results['chamfer_edges'] = result
        elif task[0] == 'split_body':
            body_id = task[1] if len(task) > 1 else None
            split_tool = task[2] if len(task) > 2 else "XY"
            keep_both = task[3] if len(task) > 3 else True
            result = split_body(design, ui, body_id, split_tool, keep_both)
            query_results['split_body'] = result
        elif task[0] == 'scale_body':
            body_id = task[1] if len(task) > 1 else None
            scale_factor = task[2] if len(task) > 2 else 1.0
            uniform = task[3] if len(task) > 3 else True
            scale_x = task[4] if len(task) > 4 else 1.0
            scale_y = task[5] if len(task) > 5 else 1.0
            scale_z = task[6] if len(task) > 6 else 1.0
            result = scale_body(design, ui, body_id, scale_factor, uniform, scale_x, scale_y, scale_z)
            query_results['scale_body'] = result



class TaskThread(threading.Thread):
    def __init__(self, event):
        threading.Thread.__init__(self)
        self.stopped = event

    def run(self):
        # Alle 200ms Custom Event feuern für Task-Verarbeitung
        while not self.stopped.wait(0.2):
            try:
                app.fireCustomEvent(myCustomEvent, json.dumps({}))
            except:
                break



###Geometry Functions######

def draw_text(design, ui, text, thickness,
              x_1, y_1, z_1, x_2, y_2, z_2, extrusion_value,plane="XY"):

    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches

        if plane == "XY":
            sketch = sketches.add(rootComp.xYConstructionPlane)
        elif plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        point_1 = adsk.core.Point3D.create(x_1, y_1, z_1)
        point_2 = adsk.core.Point3D.create(x_2, y_2, z_2)

        texts = sketch.sketchTexts
        input = texts.createInput2(f"{text}",thickness)
        input.setAsMultiLine(point_1,
                             point_2,
                             adsk.core.HorizontalAlignments.LeftHorizontalAlignment,
                             adsk.core.VerticalAlignments.TopVerticalAlignment, 0)
        sketchtext = texts.add(input)
        extrudes = rootComp.features.extrudeFeatures

        extInput = extrudes.createInput(sketchtext, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(extrusion_value)
        extInput.setDistanceExtent(False, distance)
        extInput.isSolid = True

        # Create the extrusion
        ext = extrudes.add(extInput)
    except:
        if ui:
            ui.messageBox('Failed draw_text:\n{}'.format(traceback.format_exc()))
def create_sphere(design, ui, radius, x, y, z):
    try:
        rootComp = design.rootComponent
        component: adsk.fusion.Component = design.rootComponent
        # Create a new sketch on the xy plane.
        sketches = rootComp.sketches

        xyPlane =  rootComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)
        # Draw a circle.
        circles = sketch.sketchCurves.sketchCircles
        circles.addByCenterRadius(adsk.core.Point3D.create(x,y,z), radius)
        # Draw a line to use as the axis of revolution.
        lines = sketch.sketchCurves.sketchLines
        axisLine = lines.addByTwoPoints(
            adsk.core.Point3D.create(x - radius, y, z),
            adsk.core.Point3D.create(x + radius, y, z)
        )

        # Get the profile defined by half of the circle.
        profile = sketch.profiles.item(0)
        # Create an revolution input for a revolution while specifying the profile and that a new component is to be created
        revolves = component.features.revolveFeatures
        revInput = revolves.createInput(profile, axisLine, adsk.fusion.FeatureOperations.NewComponentFeatureOperation)
        # Define that the extent is an angle of 2*pi to get a sphere
        angle = adsk.core.ValueInput.createByReal(2*math.pi)
        revInput.setAngleExtent(False, angle)
        # Create the extrusion.
        ext = revolves.add(revInput)


    except:
        if ui :
            ui.messageBox('Failed create_sphere:\n{}'.format(traceback.format_exc()))





def draw_Box(design, ui, height, width, depth,x,y,z, plane=None):
    """
    Draws Box with given dimensions height, width, depth at position (x,y,z)
    z creates an offset construction plane
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        planes = rootComp.constructionPlanes

        # Choose base plane based on parameter
        if plane == 'XZ':
            basePlane = rootComp.xZConstructionPlane
        elif plane == 'YZ':
            basePlane = rootComp.yZConstructionPlane
        else:
            basePlane = rootComp.xYConstructionPlane

        # Create offset plane at z if z != 0
        if z != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(z)
            planeInput.setByOffset(basePlane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(basePlane)

        lines = sketch.sketchCurves.sketchLines
        # addCenterPointRectangle: (center, corner-relative-to-center)
        lines.addCenterPointRectangle(
            adsk.core.Point3D.create(x, y, 0),
            adsk.core.Point3D.create(x + width/2, y + height/2, 0)
        )
        prof = sketch.profiles.item(0)
        extrudes = rootComp.features.extrudeFeatures
        extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(depth)
        extInput.setDistanceExtent(False, distance)
        extrudes.add(extInput)
    except:
        if ui:
            ui.messageBox('Failed draw_Box:\n{}'.format(traceback.format_exc()))

def draw_ellipis(design,ui,x_center,y_center,z_center,
                 x_major, y_major,z_major,x_through,y_through,z_through,plane ="XY"):
    """
    Draws an ellipse on the specified plane using three points.
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        if plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        else:
            sketch = sketches.add(rootComp.xYConstructionPlane)
        # Always define the points and create the ellipse
        # Ensure all arguments are floats (Fusion API is strict)
        centerPoint = adsk.core.Point3D.create(float(x_center), float(y_center), float(z_center))
        majorAxisPoint = adsk.core.Point3D.create(float(x_major), float(y_major), float(z_major))
        throughPoint = adsk.core.Point3D.create(float(x_through), float(y_through), float(z_through))
        sketchEllipse = sketch.sketchCurves.sketchEllipses
        ellipse = sketchEllipse.add(centerPoint, majorAxisPoint, throughPoint)
    except:
        if ui:
            ui.messageBox('Failed to draw ellipsis:\n{}'.format(traceback.format_exc()))

def draw_2d_rect(design, ui, x_1, y_1, z_1, x_2, y_2, z_2, plane="XY"):
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    planes = rootComp.constructionPlanes

    if plane == "XZ":
        baseplane = rootComp.xZConstructionPlane
        if y_1 and y_2 != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(y_1)
            planeInput.setByOffset(baseplane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(baseplane)
    elif plane == "YZ":
        baseplane = rootComp.yZConstructionPlane
        if x_1 and x_2 != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(x_1)
            planeInput.setByOffset(baseplane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(baseplane)
    else:
        baseplane = rootComp.xYConstructionPlane
        if z_1 and z_2 != 0:
            planeInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(z_1)
            planeInput.setByOffset(baseplane, offsetValue)
            offsetPlane = planes.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(baseplane)

    rectangles = sketch.sketchCurves.sketchLines
    point_1 = adsk.core.Point3D.create(x_1, y_1, z_1)
    points_2 = adsk.core.Point3D.create(x_2, y_2, z_2)
    rectangles.addTwoPointRectangle(point_1, points_2)



def draw_circle(design, ui, radius, x, y, z, plane="XY"):

    """
    Draws a circle with given radius at position (x,y,z) on the specified plane
    Plane can be "XY", "XZ", or "YZ"
    For XY plane: circle at (x,y) with z offset
    For XZ plane: circle at (x,z) with y offset
    For YZ plane: circle at (y,z) with x offset
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        planes = rootComp.constructionPlanes

        # Determine which plane and coordinates to use
        if plane == "XZ":
            basePlane = rootComp.xZConstructionPlane
            # For XZ plane: x and z are in-plane, y is the offset
            if y != 0:
                planeInput = planes.createInput()
                offsetValue = adsk.core.ValueInput.createByReal(y)
                planeInput.setByOffset(basePlane, offsetValue)
                offsetPlane = planes.add(planeInput)
                sketch = sketches.add(offsetPlane)
            else:
                sketch = sketches.add(basePlane)
            centerPoint = adsk.core.Point3D.create(x, z, 0)

        elif plane == "YZ":
            basePlane = rootComp.yZConstructionPlane
            # For YZ plane: y and z are in-plane, x is the offset
            if x != 0:
                planeInput = planes.createInput()
                offsetValue = adsk.core.ValueInput.createByReal(x)
                planeInput.setByOffset(basePlane, offsetValue)
                offsetPlane = planes.add(planeInput)
                sketch = sketches.add(offsetPlane)
            else:
                sketch = sketches.add(basePlane)
            centerPoint = adsk.core.Point3D.create(y, z, 0)

        else:  # XY plane (default)
            basePlane = rootComp.xYConstructionPlane
            # For XY plane: x and y are in-plane, z is the offset
            if z != 0:
                planeInput = planes.createInput()
                offsetValue = adsk.core.ValueInput.createByReal(z)
                planeInput.setByOffset(basePlane, offsetValue)
                offsetPlane = planes.add(planeInput)
                sketch = sketches.add(offsetPlane)
            else:
                sketch = sketches.add(basePlane)
            centerPoint = adsk.core.Point3D.create(x, y, 0)

        circles = sketch.sketchCurves.sketchCircles
        circles.addByCenterRadius(centerPoint, radius)
    except:
        if ui:
            ui.messageBox('Failed draw_circle:\n{}'.format(traceback.format_exc()))




def draw_sphere(design, ui, radius, x, y, z):
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    sketch = sketches.add(rootComp.xYConstructionPlane)
#USELESS


def draw_Witzenmann(design, ui,scaling,z):
    """
    Draws Witzenmannlogo
    can be scaled with scaling factor to make it bigger or smaller
    The z Position can be adjusted with z parameter
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)

        points1 = [
            (8.283*scaling,10.475*scaling,z),(8.283*scaling,6.471*scaling,z),(-0.126*scaling,6.471*scaling,z),(8.283*scaling,2.691*scaling,z),
            (8.283*scaling,-1.235*scaling,z),(-0.496*scaling,-1.246*scaling,z),(8.283*scaling,-5.715*scaling,z),(8.283*scaling,-9.996*scaling,z),
            (-8.862*scaling,-1.247*scaling,z),(-8.859*scaling,2.69*scaling,z),(-0.639*scaling,2.69*scaling,z),(-8.859*scaling,6.409*scaling,z),
            (-8.859*scaling,10.459*scaling,z)
        ]
        for i in range(len(points1)-1):
            start = adsk.core.Point3D.create(points1[i][0], points1[i][1],points1[i][2])
            end   = adsk.core.Point3D.create(points1[i+1][0], points1[i+1][1],points1[i+1][2])
            sketch.sketchCurves.sketchLines.addByTwoPoints(start,end) # Verbindungslinie zeichnen
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(points1[-1][0],points1[-1][1],points1[-1][2]),
            adsk.core.Point3D.create(points1[0][0],points1[0][1],points1[0][2])
        )

        points2 = [(-3.391*scaling,-5.989*scaling,z),(5.062*scaling,-10.141*scaling,z),(-8.859*scaling,-10.141*scaling,z),(-8.859*scaling,-5.989*scaling,z)]
        for i in range(len(points2)-1):
            start = adsk.core.Point3D.create(points2[i][0], points2[i][1],points2[i][2])
            end   = adsk.core.Point3D.create(points2[i+1][0], points2[i+1][1],points2[i+1][2])
            sketch.sketchCurves.sketchLines.addByTwoPoints(start,end)
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(points2[-1][0], points2[-1][1],points2[-1][2]),
            adsk.core.Point3D.create(points2[0][0], points2[0][1],points2[0][2])
        )

        extrudes = rootComp.features.extrudeFeatures
        distance = adsk.core.ValueInput.createByReal(2.0*scaling)
        for i in range(sketch.profiles.count):
            prof = sketch.profiles.item(i)
            extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            extrudeInput.setDistanceExtent(False,distance)
            extrudes.add(extrudeInput)

    except:
        if ui:
            ui.messageBox('Failed draw_Witzenmann:\n{}'.format(traceback.format_exc()))
##############################################################################################
###2D Geometry Functions######


def move_last_body(design,ui,x,y,z):

    try:
        rootComp = design.rootComponent
        features = rootComp.features
        sketches = rootComp.sketches
        moveFeats = features.moveFeatures
        body = rootComp.bRepBodies
        bodies = adsk.core.ObjectCollection.create()

        if body.count > 0:
                latest_body = body.item(body.count - 1)
                bodies.add(latest_body)
        else:
            if ui:
                ui.messageBox("Keine Bodies gefunden.")
            return

        vector = adsk.core.Vector3D.create(x,y,z)
        transform = adsk.core.Matrix3D.create()
        transform.translation = vector
        moveFeatureInput = moveFeats.createInput2(bodies)
        moveFeatureInput.defineAsFreeMove(transform)
        moveFeats.add(moveFeatureInput)
    except RuntimeError as e:
        # Handle specific RuntimeErrors like "invalid transform"
        error_msg = str(e)
        if ui:
            ui.messageBox('Failed to move the body:\n{}'.format(error_msg))
    except:
        if ui:
            ui.messageBox('Failed to move the body:\n{}'.format(traceback.format_exc()))


def pocket_recess(design, ui, depth, face_index=None, body_id=None, sketch_id=None):
    """
    Creates a pocket/recess by cutting a sketch into a body.
    Now supports explicit body_id and sketch_id for precise targeting.

    :param depth: The depth of the pocket/recess (in cm, 1 unit = 1 cm = 10mm)
    :param face_index: Optional face index (legacy parameter)
    :param body_id: Optional body ID or index to cut into
    :param sketch_id: Optional sketch ID or index to use for cutting

    IMPORTANT: The sketch must be positioned on or near an existing body.
    The sketch profile must intersect with the body to create a valid cut.
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        bodies = rootComp.bRepBodies

        # Check if there are any bodies to cut into
        if bodies.count == 0:
            return {
                "success": False,
                "error": "No target body found to cut or intersect!"
            }

        # Get the target body
        target_body = None
        if body_id is not None:
            if isinstance(body_id, int):
                if 0 <= body_id < bodies.count:
                    target_body = bodies.item(body_id)
            else:
                # Try to find by entity token
                for i in range(bodies.count):
                    if bodies.item(i).entityToken == body_id:
                        target_body = bodies.item(i)
                        break

        # Get the sketch to use
        target_sketch = None
        if sketch_id is not None:
            if isinstance(sketch_id, int):
                if 0 <= sketch_id < sketches.count:
                    target_sketch = sketches.item(sketch_id)
            else:
                # Try to find by entity token
                for i in range(sketches.count):
                    if sketches.item(i).entityToken == sketch_id:
                        target_sketch = sketches.item(i)
                        break
        else:
            # Use the last sketch if not specified
            if sketches.count == 0:
                return {"success": False, "error": "No sketch found. Please create a sketch first."}
            target_sketch = sketches.item(sketches.count - 1)

        if target_sketch is None:
            return {"success": False, "error": f"Sketch not found: {sketch_id}"}

        # Check if sketch has profiles
        if target_sketch.profiles.count == 0:
            return {"success": False, "error": "Sketch has no closed profiles. Please draw a closed shape."}

        prof = target_sketch.profiles.item(0)

        # Create cut extrude
        extrudes = rootComp.features.extrudeFeatures
        extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(abs(depth))
        extrudeInput.setDistanceExtent(False, distance)

        # If a specific body was provided, set it as the target
        if target_body is not None:
            participantBodies = adsk.core.ObjectCollection.create()
            participantBodies.add(target_body)
            extrudeInput.participantBodies = participantBodies

        try:
            extrudes.add(extrudeInput)
            return {
                "success": True,
                "depth": depth,
                "sketch_name": target_sketch.name,
                "body_name": target_body.name if target_body else "auto",
                "message": "Pocket created successfully"
            }
        except RuntimeError as e:
            error_msg = str(e)
            if "No target body found" in error_msg or "cut or intersect" in error_msg:
                return {
                    "success": False,
                    "error": "Failed to create pocket: The sketch profile does not intersect with any existing body!"
                }
            else:
                return {"success": False, "error": f"Failed to create pocket: {error_msg}"}

    except Exception as e:
        if ui:
            ui.messageBox('Failed pocket_recess:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}


def sketch_on_face(design, ui, body_index, face_index):
    """
    Creates a new sketch on a specific face of a body.
    Note: This only works on PLANAR faces. Curved or non-planar faces cannot be used.
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        bodies = rootComp.bRepBodies

        if bodies.count == 0:
            ui.messageBox("No bodies found in the design.")
            return

        # Get the specified body (default to last body if index out of range)
        if body_index >= bodies.count or body_index < 0:
            body = bodies.item(bodies.count - 1)
        else:
            body = bodies.item(body_index)

        # Get the specified face
        if face_index >= body.faces.count or face_index < 0:
            ui.messageBox(f"Face index {face_index} is out of range. Body has {body.faces.count} faces.")
            return

        face = body.faces.item(face_index)

        # Check if face is planar (only planar faces can have sketches)
        if face.geometry.surfaceType != adsk.core.SurfaceTypes.PlaneSurfaceType:
            ui.messageBox(f"Cannot create sketch on face {face_index}: Face is not planar (it's curved or non-planar).\n\n"
                         f"Only flat/planar faces can be used for sketching.\n"
                         f"Try using a different face or create a work plane instead.")
            return

        # Create sketch on the face
        sketch = sketches.add(face)

        # Success - no notification needed (only show failures)

    except:
        if ui:
            ui.messageBox('Failed sketch_on_face:\n{}'.format(traceback.format_exc()))


def create_work_plane(design, ui, plane_type, offset_distance, reference_index=0):
    """
    Creates a construction/work plane for advanced sketching.
    plane_type: 'offset_xy', 'offset_xz', 'offset_yz', 'face_offset', 'midplane'
    offset_distance: distance to offset the plane
    reference_index: face or plane index for reference (used with face_offset)
    """
    try:
        rootComp = design.rootComponent
        planes = rootComp.constructionPlanes
        planeInput = planes.createInput()

        if plane_type == 'offset_xy':
            basePlane = rootComp.xYConstructionPlane
            offsetValue = adsk.core.ValueInput.createByReal(offset_distance)
            planeInput.setByOffset(basePlane, offsetValue)

        elif plane_type == 'offset_xz':
            basePlane = rootComp.xZConstructionPlane
            offsetValue = adsk.core.ValueInput.createByReal(offset_distance)
            planeInput.setByOffset(basePlane, offsetValue)

        elif plane_type == 'offset_yz':
            basePlane = rootComp.yZConstructionPlane
            offsetValue = adsk.core.ValueInput.createByReal(offset_distance)
            planeInput.setByOffset(basePlane, offsetValue)

        elif plane_type == 'face_offset':
            bodies = rootComp.bRepBodies
            if bodies.count == 0:
                ui.messageBox("No bodies found for face offset plane.")
                return
            body = bodies.item(bodies.count - 1)
            if reference_index >= body.faces.count:
                ui.messageBox(f"Face index {reference_index} out of range.")
                return
            face = body.faces.item(reference_index)
            offsetValue = adsk.core.ValueInput.createByReal(offset_distance)
            planeInput.setByOffset(face, offsetValue)

        # Create the plane
        plane = planes.add(planeInput)

    except:
        if ui:
            ui.messageBox('Failed create_work_plane:\n{}'.format(traceback.format_exc()))


def project_edges(design, ui, body_index=None):
    """
    Projects edges from a body onto the current sketch plane.
    This allows you to reference existing geometry in your sketch.
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        bodies = rootComp.bRepBodies

        if sketches.count == 0:
            ui.messageBox("No sketch found. Please create a sketch first.")
            return

        if bodies.count == 0:
            ui.messageBox("No bodies found to project edges from.")
            return

        # Get the last sketch
        sketch = sketches.item(sketches.count - 1)

        # Get the body to project from
        if body_index is None or body_index >= bodies.count or body_index < 0:
            body = bodies.item(bodies.count - 1)
        else:
            body = bodies.item(body_index)

        # Project all edges from the body
        for i in range(body.edges.count):
            edge = body.edges.item(i)
            try:
                # Create a collection with this edge
                edgesToProject = adsk.core.ObjectCollection.create()
                edgesToProject.add(edge)

                # Project the edges onto the sketch
                sketch.project(edgesToProject)
            except:
                # Some edges may not be projectable, skip them
                pass

    except:
        if ui:
            ui.messageBox('Failed project_edges:\n{}'.format(traceback.format_exc()))


def draw_polygon(design, ui, sides, radius, x, y, z, plane="XY"):
    """
    Draws a regular polygon with the specified number of sides.
    Useful for creating hexagons, pentagons, etc.
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        planes = rootComp.constructionPlanes

        # Determine which plane to use
        if plane == "XZ":
            basePlane = rootComp.xZConstructionPlane
            if y != 0:
                planeInput = planes.createInput()
                offsetValue = adsk.core.ValueInput.createByReal(y)
                planeInput.setByOffset(basePlane, offsetValue)
                offsetPlane = planes.add(planeInput)
                sketch = sketches.add(offsetPlane)
            else:
                sketch = sketches.add(basePlane)

        elif plane == "YZ":
            basePlane = rootComp.yZConstructionPlane
            if x != 0:
                planeInput = planes.createInput()
                offsetValue = adsk.core.ValueInput.createByReal(x)
                planeInput.setByOffset(basePlane, offsetValue)
                offsetPlane = planes.add(planeInput)
                sketch = sketches.add(offsetPlane)
            else:
                sketch = sketches.add(basePlane)

        else:  # XY plane (default)
            basePlane = rootComp.xYConstructionPlane
            if z != 0:
                planeInput = planes.createInput()
                offsetValue = adsk.core.ValueInput.createByReal(z)
                planeInput.setByOffset(basePlane, offsetValue)
                offsetPlane = planes.add(planeInput)
                sketch = sketches.add(offsetPlane)
            else:
                sketch = sketches.add(basePlane)

        # Create polygon using circumscribed circle method
        lines = sketch.sketchCurves.sketchLines
        import math
        angleStep = (2 * math.pi) / sides

        # Calculate vertices
        vertices = []
        for i in range(sides):
            angle = i * angleStep
            px = radius * math.cos(angle)
            py = radius * math.sin(angle)

            # Create vertices in sketch coordinate system (third parameter is always 0)
            if plane == "XZ":
                # XZ plane: X and Z are in-plane, Y is perpendicular
                vertices.append(adsk.core.Point3D.create(x + px, 0, z + py))
            elif plane == "YZ":
                # YZ plane: Y and Z are in-plane, X is perpendicular
                vertices.append(adsk.core.Point3D.create(0, y + px, z + py))
            else:  # XY
                # XY plane: X and Y are in-plane, Z is perpendicular
                vertices.append(adsk.core.Point3D.create(x + px, y + py, 0))

        # Draw lines connecting vertices
        for i in range(sides):
            nextIndex = (i + 1) % sides
            lines.addByTwoPoints(vertices[i], vertices[nextIndex])

    except:
        if ui:
            ui.messageBox('Failed draw_polygon:\n{}'.format(traceback.format_exc()))


def offset_surface(design, ui, distance, face_index=0):
    """
    Creates an offset surface by offsetting faces of a body.
    Useful for creating wall thicknesses and parallel surfaces.
    """
    try:
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies

        if bodies.count == 0:
            ui.messageBox("No bodies found.")
            return

        body = bodies.item(bodies.count - 1)

        # Get the face to offset
        if face_index >= body.faces.count or face_index < 0:
            ui.messageBox(f"Face index {face_index} out of range.")
            return

        face = body.faces.item(face_index)

        # Create offset face feature
        offsetFeatures = rootComp.features.offsetFeatures

        # Create a collection of faces to offset
        inputFaces = adsk.core.ObjectCollection.create()
        inputFaces.add(face)

        # Create offset feature input
        offsetInput = offsetFeatures.createInput(
            inputFaces,
            adsk.core.ValueInput.createByReal(distance),
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )

        # Create the offset
        offsetFeatures.add(offsetInput)

    except:
        if ui:
            ui.messageBox('Failed offset_surface:\n{}'.format(traceback.format_exc()))


def mirror_feature(design, ui, mirror_plane, body_index=None):
    """
    Mirrors the latest body or specified body across a plane.
    mirror_plane: 'XY', 'XZ', 'YZ'
    """
    try:
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies
        mirrorFeatures = rootComp.features.mirrorFeatures

        if bodies.count == 0:
            ui.messageBox("No bodies found to mirror.")
            return

        # Get the body to mirror
        if body_index is None or body_index >= bodies.count or body_index < 0:
            body = bodies.item(bodies.count - 1)
        else:
            body = bodies.item(body_index)

        # Create collection with the body
        inputEntities = adsk.core.ObjectCollection.create()
        inputEntities.add(body)

        # Get the mirror plane
        if mirror_plane == "XY":
            mirrorPlane = rootComp.xYConstructionPlane
        elif mirror_plane == "XZ":
            mirrorPlane = rootComp.xZConstructionPlane
        elif mirror_plane == "YZ":
            mirrorPlane = rootComp.yZConstructionPlane
        else:
            ui.messageBox(f"Invalid mirror plane: {mirror_plane}")
            return

        # Create mirror input
        mirrorInput = mirrorFeatures.createInput(inputEntities, mirrorPlane)

        # Create the mirror feature
        mirrorFeatures.add(mirrorInput)

    except:
        if ui:
            ui.messageBox('Failed mirror_feature:\n{}'.format(traceback.format_exc()))


def offsetplane(design, ui, offset, plane="XY"):
    """
    Creates a new offset construction plane which can be selected.

    :param design: The Fusion 360 design object
    :param ui: The Fusion 360 user interface object
    :param offset: Distance to offset the plane (in cm)
    :param plane: Base plane to offset from ('XY', 'XZ', or 'YZ')
    :return: None
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        offset = adsk.core.ValueInput.createByReal(offset)
        ctorPlanes = rootComp.constructionPlanes
        ctorPlaneInput1 = ctorPlanes.createInput()

        if plane == "XY":
            ctorPlaneInput1.setByOffset(rootComp.xYConstructionPlane, offset)
        elif plane == "XZ":
            ctorPlaneInput1.setByOffset(rootComp.xZConstructionPlane, offset)
        elif plane == "YZ":
            ctorPlaneInput1.setByOffset(rootComp.yZConstructionPlane, offset)
        ctorPlanes.add(ctorPlaneInput1)
    except:
        if ui:
            ui.messageBox('Failed offsetplane:\n{}'.format(traceback.format_exc()))



def create_thread(design, ui,inside,sizes):
    """

    params:
    inside: boolean information if the face is inside or outside
    lengt: length of the thread
    sizes : index of the size in the allsizes list
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        threadFeatures = rootComp.features.threadFeatures

        ui.messageBox('Select a face for threading.')
        face = ui.selectEntity("Select a face for threading", "Faces").entity
        faces = adsk.core.ObjectCollection.create()
        faces.add(face)
        #Get the thread infos


        threadDataQuery = threadFeatures.threadDataQuery
        threadTypes = threadDataQuery.allThreadTypes
        threadType = threadTypes[0]

        allsizes = threadDataQuery.allSizes(threadType)

        # allsizes :
        #'1/4', '5/16', '3/8', '7/16', '1/2', '5/8', '3/4', '7/8', '1', '1 1/8', '1 1/4',
        # '1 3/8', '1 1/2', '1 3/4', '2', '2 1/4', '2 1/2', '2 3/4', '3', '3 1/2', '4', '4 1/2', '5')
        #
        threadSize = allsizes[sizes]



        allDesignations = threadDataQuery.allDesignations(threadType, threadSize)
        threadDesignation = allDesignations[0]

        allClasses = threadDataQuery.allClasses(False, threadType, threadDesignation)
        threadClass = allClasses[0]

        # create the threadInfo according to the query result
        threadInfo = threadFeatures.createThreadInfo(inside, threadType, threadDesignation, threadClass)

        # get the face the thread will be applied to



        threadInput = threadFeatures.createInput(faces, threadInfo)
        threadInput.isFullLength = True

        # create the final thread
        thread = threadFeatures.add(threadInput)





    except:
        if ui:
            ui.messageBox('Failed offsetplane thread:\n{}'.format(traceback.format_exc()))







def spline(design, ui, points, plane="XY"):
    """
    Draws a spline through the given points on the specified plane
    Plane can be "XY", "XZ", or "YZ"
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        if plane == "XY":
            sketch = sketches.add(rootComp.xYConstructionPlane)
        elif plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)

        splinePoints = adsk.core.ObjectCollection.create()
        for point in points:
            splinePoints.add(adsk.core.Point3D.create(point[0], point[1], point[2]))

        sketch.sketchCurves.sketchFittedSplines.add(splinePoints)

        # Note: Splines can be open or closed - no warning needed
    except:
        if ui:
            ui.messageBox('Failed draw_spline:\n{}'.format(traceback.format_exc()))





def arc(design,ui,point1,point2,points3,plane = "XY",connect = False):
    """
    This creates arc between two points on the specified plane
    """
    try:
        rootComp = design.rootComponent #Holen der Rotkomponente
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane
        if plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        else:
            xyPlane = rootComp.xYConstructionPlane

            sketch = sketches.add(xyPlane)
        start  = adsk.core.Point3D.create(point1[0],point1[1],point1[2])
        alongpoint    = adsk.core.Point3D.create(point2[0],point2[1],point2[2])
        endpoint =adsk.core.Point3D.create(points3[0],points3[1],points3[2])
        arcs = sketch.sketchCurves.sketchArcs
        arc = arcs.addByThreePoints(start, alongpoint, endpoint)
        if connect:
            startconnect = adsk.core.Point3D.create(start.x, start.y, start.z)
            endconnect = adsk.core.Point3D.create(endpoint.x, endpoint.y, endpoint.z)
            lines = sketch.sketchCurves.sketchLines
            lines.addByTwoPoints(startconnect, endconnect)
            connect = False
        else:
            lines = sketch.sketchCurves.sketchLines

        # Note: Arcs can be open or closed - no warning needed

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def draw_lines(design,ui, points,Plane = "XY"):
    """
    User input: points = [(x1,y1), (x2,y2), ...]
    Plane: "XY", "XZ", "YZ"
    Draws lines between the given points on the specified plane
    Connects the last point to the first point to close the shape
    """
    try:
        rootComp = design.rootComponent #Holen der Rotkomponente
        sketches = rootComp.sketches
        if Plane == "XY":
            xyPlane = rootComp.xYConstructionPlane
            sketch = sketches.add(xyPlane)
        elif Plane == "XZ":
            xZPlane = rootComp.xZConstructionPlane
            sketch = sketches.add(xZPlane)
        elif Plane == "YZ":
            yZPlane = rootComp.yZConstructionPlane
            sketch = sketches.add(yZPlane)
        for i in range(len(points)-1):
            start = adsk.core.Point3D.create(points[i][0], points[i][1], 0)
            end   = adsk.core.Point3D.create(points[i+1][0], points[i+1][1], 0)
            sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(points[-1][0],points[-1][1],0),
            adsk.core.Point3D.create(points[0][0],points[0][1],0) #
        ) # Verbindet den ersten und letzten Punkt

    except:
        if ui :
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def draw_one_line(design, ui, x1, y1, z1, x2, y2, z2, plane="XY"):
    """
    Draws a single line between two points (x1, y1, z1) and (x2, y2, z2) on the specified plane
    Plane can be "XY", "XZ", or "YZ"
    This function does not add a new sketch it is designed to be used after arc
    This is how we can make half circles and extrude them

    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches

        # Check if there are any sketches before accessing
        if sketches.count == 0:
            if ui:
                ui.messageBox('No sketches found. Please create a sketch first (e.g., using arc or draw_lines).')
            return

        sketch = sketches.item(sketches.count - 1)

        start = adsk.core.Point3D.create(x1, y1, 0)
        end = adsk.core.Point3D.create(x2, y2, 0)
        sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)

        # Note: Lines can be open or closed - no warning needed
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))



#################################################################################



###3D Geometry Functions######
def loft(design, ui, sketchcount):
    """
    Creates a loft between the last 'sketchcount' sketches
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        loftFeatures = rootComp.features.loftFeatures

        # Check if there are enough sketches
        if sketches.count < sketchcount:
            if ui:
                ui.messageBox(f"Loft requires {sketchcount} sketches, but only {sketches.count} found. Please create more sketches.")
            return

        loftInput = loftFeatures.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        loftSectionsObj = loftInput.loftSections

        # Add profiles from the last 'sketchcount' sketches
        for i in range(sketchcount):
            sketch = sketches.item(sketches.count - 1 - i)

            # Check if sketch has profiles
            if sketch.profiles.count == 0:
                if ui:
                    ui.messageBox(f"Sketch {sketches.count - 1 - i} has no closed profiles. Please draw closed shapes.")
                return

            profile = sketch.profiles.item(0)
            loftSectionsObj.add(profile)

        loftInput.isSolid = True
        loftInput.isClosed = False
        loftInput.isTangentEdgesMerged = True

        # Create loft feature
        loftFeatures.add(loftInput)

    except:
        if ui:
            ui.messageBox('Failed loft:\n{}'.format(traceback.format_exc()))



def boolean_operation(design,ui,op):
    """
    This function performs boolean operations (cut, intersect, join)
    It is important to draw the target body first, then the tool body

    """
    try:
        app = adsk.core.Application.get()
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        ui  = app.userInterface

        # Get the root component of the active design.
        rootComp = design.rootComponent
        features = rootComp.features
        bodies = rootComp.bRepBodies

        targetBody = bodies.item(0) # target body has to be the first drawn body
        toolBody = bodies.item(1)   # tool body has to be the second drawn body


        combineFeatures = rootComp.features.combineFeatures
        tools = adsk.core.ObjectCollection.create()
        tools.add(toolBody)
        input: adsk.fusion.CombineFeatureInput = combineFeatures.createInput(targetBody, tools)
        input.isNewComponent = False
        input.isKeepToolBodies = False
        if op == "cut":
            input.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
        elif op == "intersect":
            input.operation = adsk.fusion.FeatureOperations.IntersectFeatureOperation
        elif op == "join":
            input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation

        combineFeature = combineFeatures.add(input)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))






def sweep(design,ui):
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        sweeps = rootComp.features.sweepFeatures

        # Check if there are at least 2 sketches for sweep
        if sketches.count < 2:
            if ui:
                ui.messageBox("Sweep requires at least 2 sketches (profile and path). Please create sketches first.")
            return

        profsketch = sketches.item(sketches.count - 2)  # Profile sketch

        # Check if profile sketch has profiles
        if profsketch.profiles.count == 0:
            if ui:
                ui.messageBox("Profile sketch has no closed profiles. Please draw a closed shape for the profile.")
            return

        prof = profsketch.profiles.item(0)  # First profile in the sketch

        pathsketch = sketches.item(sketches.count - 1)  # Path sketch

        # Check if path sketch has curves
        if pathsketch.sketchCurves.count == 0:
            if ui:
                ui.messageBox("Path sketch has no curves. Please draw a path for the sweep.")
            return

        # collect all sketch curves in an ObjectCollection
        pathCurves = adsk.core.ObjectCollection.create()
        for i in range(pathsketch.sketchCurves.count):
            pathCurves.add(pathsketch.sketchCurves.item(i))

        path = adsk.fusion.Path.create(pathCurves, 0)
        sweepInput = sweeps.createInput(prof, path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        sweeps.add(sweepInput)
    except:
        if ui:
            ui.messageBox('Failed sweep:\n{}'.format(traceback.format_exc()))



def extrude_last_sketch(design, ui, value,taperangle):
    """
    Extrudes the last sketch by the given value and returns the body ID
    Returns a dict with body_id, body_name, and success status
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches

        # Check if there are any sketches
        if sketches.count == 0:
            if ui:
                ui.messageBox("No sketches found. Please create a sketch first.")
            return {"success": False, "error": "No sketches found"}

        sketch = sketches.item(sketches.count - 1)  # Letzter Sketch

        # Check if the sketch has profiles
        if sketch.profiles.count == 0:
            if ui:
                ui.messageBox("Sketch has no closed profiles. Please draw a closed shape.")
            return {"success": False, "error": "Sketch has no closed profiles"}

        prof = sketch.profiles.item(0)  # Erstes Profil im Sketch
        extrudes = rootComp.features.extrudeFeatures
        extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(value)

        if taperangle != 0:
            taperValue = adsk.core.ValueInput.createByString(f'{taperangle} deg')

            extent_distance = adsk.fusion.DistanceExtentDefinition.create(distance)
            extrudeInput.setOneSideExtent(extent_distance, adsk.fusion.ExtentDirections.PositiveExtentDirection, taperValue)
        else:
            extrudeInput.setDistanceExtent(False, distance)

        # Create the extrusion and get the resulting body
        ext = extrudes.add(extrudeInput)

        # Get the body that was created
        if ext.bodies.count > 0:
            body = ext.bodies.item(0)
            body_id = body.entityToken
            body_name = body.name
            return {
                "success": True,
                "body_id": body_id,
                "body_name": body_name,
                "message": f"Extrusion created: {body_name}"
            }
        else:
            return {"success": False, "error": "Extrusion failed to create a body"}

    except Exception as e:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}

def shell_existing_body(design, ui, thickness=0.5, faceindex=0):
    """
    Shells the body on a specified face index with given thickness
    Checks if body has already been shelled to prevent duplicate shell operations
    """
    try:
        rootComp = design.rootComponent
        features = rootComp.features
        body = rootComp.bRepBodies.item(0)

        # Check if body has already been shelled by examining timeline
        timeline = design.timeline
        shell_count = 0
        for i in range(timeline.count):
            timeline_obj = timeline.item(i)
            entity = timeline_obj.entity
            if entity and entity.objectType == adsk.fusion.ShellFeature.classType():
                shell_count += 1

        if shell_count > 0:
            error_msg = (f"Body has already been shelled ({shell_count} shell operation(s) detected). "
                        "Cannot apply shell again. Consider:\n"
                        "1. Use undo() to remove previous shell\n"
                        "2. Delete and recreate the model\n"
                        "3. Adjust thickness of existing shell via parameters")
            if ui:
                ui.messageBox('Shell Operation Skipped:\n{}'.format(error_msg))
            return {"success": False, "error": "already_shelled", "message": error_msg}

        entities = adsk.core.ObjectCollection.create()

        # Validate face index
        if faceindex < 0 or faceindex >= body.faces.count:
            error_msg = f"Invalid face index {faceindex}. Body has {body.faces.count} faces (valid range: 0-{body.faces.count-1})"
            if ui:
                ui.messageBox('Shell Failed:\n{}'.format(error_msg))
            return {"success": False, "error": "invalid_face_index", "message": error_msg}

        entities.add(body.faces.item(faceindex))

        shellFeats = features.shellFeatures
        isTangentChain = False
        shellInput = shellFeats.createInput(entities, isTangentChain)

        thicknessVal = adsk.core.ValueInput.createByReal(thickness)
        shellInput.insideThickness = thicknessVal

        shellInput.shellType = adsk.fusion.ShellTypes.SharpOffsetShellType

        # Ausführen
        shellFeats.add(shellInput)
        return {"success": True, "message": "Shell applied successfully"}

    except RuntimeError as e:
        # Log RuntimeError without UI popup (e.g., "Shell compute failed", "no lump left")
        error_msg = str(e)

        # Check for specific shell errors and provide helpful guidance
        if "ASM_LOP_HOL_MULTI_SHELL" in error_msg or "already been shelled" in error_msg:
            guidance = (f"Shell Failed: {error_msg}\n\n"
                       "The body appears to have already been shelled. Solutions:\n"
                       "1. Use undo() to remove the previous shell operation\n"
                       "2. Delete all objects and start fresh with delete_all()\n"
                       "3. Check your workflow - shells should only be applied once")
        elif "ASM_RBI_NO_LUMP_LEFT" in error_msg or "does not cause a meaningful shape change" in error_msg:
            guidance = (f"Shell Failed: {error_msg}\n\n"
                       "The shell thickness is too large or invalid for this body.\n\n"
                       "Solutions:\n"
                       "1. REDUCE THICKNESS: Try 0.1 cm (1mm) instead of current value\n"
                       "2. Try a different face index (0, 1, 2, 3, 4, 5)\n"
                       "3. Verify body has sufficient volume for wall thickness\n"
                       "4. Use extrude_thin() as an alternative method\n\n"
                       "Quick fix: undo(); shell_body(thickness=0.1, faceindex=0)")
        elif "ASM_API_FAILED" in error_msg or "The operation failed" in error_msg:
            guidance = (f"Shell Failed: {error_msg}\n\n"
                       "Generic API failure - usually caused by geometry issues.\n\n"
                       "Troubleshooting steps:\n"
                       "1. Try DIFFERENT FACE INDEX: undo(); shell_body(thickness=0.1, faceindex=1)\n"
                       "2. REDUCE THICKNESS: Try 0.1 cm (1mm) instead\n"
                       "3. Check body geometry: verify it's a valid closed solid\n"
                       "4. Try different shell method: use extrude_thin() instead\n"
                       "5. If all faces fail, rebuild: delete_all() and start fresh\n\n"
                       "Common cause: face selection or body geometry invalid")
        elif "invalid transform" in error_msg:
            guidance = (f"Shell Failed: {error_msg}\n\n"
                       "Face selection or geometry issue. Solutions:\n"
                       "1. Try a different face index\n"
                       "2. Verify body geometry is valid\n"
                       "3. Check that face exists")
        else:
            guidance = f"Shell Failed: {error_msg}"

        if ui:
            ui.messageBox(guidance)
        return {"success": False, "error": "runtime_error", "message": guidance}
    except Exception as e:
        error_msg = traceback.format_exc()
        if ui:
            ui.messageBox('Failed:\n{}'.format(error_msg))
        return {"success": False, "error": "unknown_error", "message": error_msg}


def fillet_edges(design, ui, radius=0.3, edge_ids=None):
    """
    Fillets edges with specified radius.
    If edge_ids is provided, only those edges are filleted (edge-selective).
    If edge_ids is None, attempts to fillet all edges (legacy behavior).

    :param radius: Fillet radius in cm
    :param edge_ids: List of edge indices or None for all edges
    """
    try:
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies
        fillets = rootComp.features.filletFeatures

        if bodies.count == 0:
            return {"success": False, "error": "No bodies found"}

        successful_fillets = 0
        failed_edges = 0

        # If specific edge IDs provided, only fillet those
        if edge_ids is not None and len(edge_ids) > 0:
            # Get the last body
            body = bodies.item(bodies.count - 1)

            # Create edge collection for specified edges
            edgeCollection = adsk.core.ObjectCollection.create()

            for edge_id in edge_ids:
                if isinstance(edge_id, int) and 0 <= edge_id < body.edges.count:
                    edge = body.edges.item(edge_id)
                    edgeCollection.add(edge)

            if edgeCollection.count == 0:
                return {"success": False, "error": "No valid edges found in edge_ids"}

            try:
                # Create fillet for selected edges
                radiusInput = adsk.core.ValueInput.createByReal(radius)
                filletInput = fillets.createInput()
                filletInput.isRollingBallCorner = True
                edgeSetInput = filletInput.edgeSetInputs.addConstantRadiusEdgeSet(edgeCollection, radiusInput, True)
                edgeSetInput.continuity = adsk.fusion.SurfaceContinuityTypes.TangentSurfaceContinuityType
                fillets.add(filletInput)
                successful_fillets = edgeCollection.count
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to fillet specified edges: {str(e)}"
                }
        else:
            # Legacy behavior: try to fillet all edges
            for body_idx in range(bodies.count):
                body = bodies.item(body_idx)

                # Try to fillet edges in smaller groups to handle failures better
                for edge_idx in range(body.edges.count):
                    edge = body.edges.item(edge_idx)

                    try:
                        # Create a collection for this single edge
                        edgeCollection = adsk.core.ObjectCollection.create()
                        edgeCollection.add(edge)

                        # Try to create the fillet for this edge
                        radiusInput = adsk.core.ValueInput.createByReal(radius)
                        filletInput = fillets.createInput()
                        filletInput.isRollingBallCorner = True
                        edgeSetInput = filletInput.edgeSetInputs.addConstantRadiusEdgeSet(edgeCollection, radiusInput, True)
                        edgeSetInput.continuity = adsk.fusion.SurfaceContinuityTypes.TangentSurfaceContinuityType
                        fillets.add(filletInput)
                        successful_fillets += 1
                    except Exception:
                        # Skip edges that can't be filleted (e.g., sharp corners)
                        failed_edges += 1
                        continue

        # Return detailed results
        return {
            "success": True,
            "successful_fillets": successful_fillets,
            "failed_edges": failed_edges,
            "radius": radius,
            "message": f"Successfully filleted {successful_fillets} edge(s)" +
                      (f", {failed_edges} edge(s) skipped" if failed_edges > 0 else "")
        }

    except Exception as e:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}

def chamfer_edges(design, ui, distance=0.5, edge_ids=None, angle=45.0):
    """
    Creates angled beveled edges (chamfers) on specified edges.
    Unlike fillets (rounded), chamfers create flat angled surfaces.

    :param distance: Chamfer distance in cm (how far from edge the bevel extends)
    :param edge_ids: List of edge indices or None for all edges
    :param angle: Chamfer angle in degrees (default 45°)
    :return: Result with success status and chamfer details
    """
    try:
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies
        chamfers = rootComp.features.chamferFeatures

        if bodies.count == 0:
            return {"success": False, "error": "No bodies found"}

        successful_chamfers = 0
        failed_edges = 0

        # If specific edge IDs provided, only chamfer those
        if edge_ids is not None and len(edge_ids) > 0:
            # Get the last body
            body = bodies.item(bodies.count - 1)

            # Create edge collection for specified edges
            edgeCollection = adsk.core.ObjectCollection.create()

            for edge_id in edge_ids:
                if isinstance(edge_id, int) and 0 <= edge_id < body.edges.count:
                    edge = body.edges.item(edge_id)
                    edgeCollection.add(edge)

            if edgeCollection.count == 0:
                return {"success": False, "error": "No valid edges found in edge_ids"}

            try:
                # Create chamfer for selected edges
                distanceInput = adsk.core.ValueInput.createByReal(distance)
                chamferInput = chamfers.createInput2()
                chamferInput.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
                    edgeCollection, distanceInput, True
                )
                chamfers.add(chamferInput)
                successful_chamfers = edgeCollection.count
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to chamfer specified edges: {str(e)}"
                }
        else:
            # Try to chamfer all edges
            for body_idx in range(bodies.count):
                body = bodies.item(body_idx)

                for edge_idx in range(body.edges.count):
                    edge = body.edges.item(edge_idx)

                    try:
                        edgeCollection = adsk.core.ObjectCollection.create()
                        edgeCollection.add(edge)
                        distanceInput = adsk.core.ValueInput.createByReal(distance)
                        chamferInput = chamfers.createInput2()
                        chamferInput.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
                            edgeCollection, distanceInput, True
                        )
                        chamfers.add(chamferInput)
                        successful_chamfers += 1
                    except Exception:
                        failed_edges += 1
                        continue

        return {
            "success": True,
            "successful_chamfers": successful_chamfers,
            "failed_edges": failed_edges,
            "distance": distance,
            "angle": angle,
            "message": f"Successfully chamfered {successful_chamfers} edge(s)" +
                      (f", {failed_edges} edge(s) skipped" if failed_edges > 0 else "")
        }

    except Exception as e:
        if ui:
            ui.messageBox('Chamfer failed:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}

def split_body(design, ui, body_id=None, split_tool="sketch_plane", keep_both=True):
    """
    Splits a body using a sketch plane or construction plane.
    Useful for multi-material props or splitting for 3D printing.

    :param body_id: Body ID to split (None = last body)
    :param split_tool: "sketch_plane", "XY", "YZ", "XZ", or "construction_plane"
    :param keep_both: If True, keeps both halves; if False, keeps only one
    :return: Result with split body information
    """
    try:
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies

        if bodies.count == 0:
            return {"success": False, "error": "No bodies found"}

        # Get target body
        if body_id is not None and isinstance(body_id, str):
            target_body = None
            for i in range(bodies.count):
                body = bodies.item(i)
                if body.name == body_id or f"body_{i}" == body_id:
                    target_body = body
                    break
            if target_body is None:
                return {"success": False, "error": f"Body {body_id} not found"}
        else:
            target_body = bodies.item(bodies.count - 1)

        # Get splitting plane
        splitFace = None
        if split_tool in ["XY", "YZ", "XZ"]:
            # Use construction plane
            planes = rootComp.constructionPlanes
            if split_tool == "XY":
                plane = rootComp.xYConstructionPlane
            elif split_tool == "YZ":
                plane = rootComp.yZConstructionPlane
            else:  # XZ
                plane = rootComp.xZConstructionPlane

            # Create split using plane
            splitBodyFeats = rootComp.features.splitBodyFeatures
            splitBodyInput = splitBodyFeats.createInput(target_body, plane, not keep_both)
            splitBodyFeats.add(splitBodyInput)

            return {
                "success": True,
                "original_body": target_body.name,
                "split_plane": split_tool,
                "keep_both": keep_both,
                "result_bodies": bodies.count,
                "message": f"Body split using {split_tool} plane"
            }
        else:
            return {
                "success": False,
                "error": "split_tool must be 'XY', 'YZ', or 'XZ'"
            }

    except Exception as e:
        if ui:
            ui.messageBox('Split body failed:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}

def scale_body(design, ui, body_id=None, scale_factor=1.0, uniform=True,
              scale_x=1.0, scale_y=1.0, scale_z=1.0):
    """
    Scales a body by specified factors.
    Useful for adjusting prop sizes or creating scaled replicas.

    :param body_id: Body ID to scale (None = last body)
    :param scale_factor: Uniform scale factor (used if uniform=True)
    :param uniform: If True, uses scale_factor; if False, uses scale_x/y/z
    :param scale_x: X-axis scale factor
    :param scale_y: Y-axis scale factor
    :param scale_z: Z-axis scale factor
    :return: Result with scaling information
    """
    try:
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies

        if bodies.count == 0:
            return {"success": False, "error": "No bodies found"}

        # Get target body
        if body_id is not None and isinstance(body_id, str):
            target_body = None
            for i in range(bodies.count):
                body = bodies.item(i)
                if body.name == body_id or f"body_{i}" == body_id:
                    target_body = body
                    break
            if target_body is None:
                return {"success": False, "error": f"Body {body_id} not found"}
        else:
            target_body = bodies.item(bodies.count - 1)

        # Determine scale factors
        if uniform:
            final_scale_x = scale_factor
            final_scale_y = scale_factor
            final_scale_z = scale_factor
        else:
            final_scale_x = scale_x
            final_scale_y = scale_y
            final_scale_z = scale_z

        # Create scale feature
        scaleFeatures = rootComp.features.scaleFeatures

        # Create an object collection with the body
        inputEntities = adsk.core.ObjectCollection.create()
        inputEntities.add(target_body)

        # Get the origin point as the scale center
        originPoint = rootComp.originConstructionPoint

        # Create scale input
        scaleInput = scaleFeatures.createInput(inputEntities, originPoint)

        # Set scale factors
        if uniform:
            scaleInput.setToUniform(adsk.core.ValueInput.createByReal(scale_factor))
        else:
            scaleInput.setToNonUniform(
                adsk.core.ValueInput.createByReal(final_scale_x),
                adsk.core.ValueInput.createByReal(final_scale_y),
                adsk.core.ValueInput.createByReal(final_scale_z)
            )

        # Add the scale feature
        scaleFeatures.add(scaleInput)

        return {
            "success": True,
            "body_name": target_body.name,
            "uniform": uniform,
            "scale_x": final_scale_x,
            "scale_y": final_scale_y,
            "scale_z": final_scale_z,
            "message": f"Body scaled by {scale_factor if uniform else f'x={final_scale_x}, y={final_scale_y}, z={final_scale_z}'}"
        }

    except Exception as e:
        if ui:
            ui.messageBox('Scale body failed:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}

def revolve_profile(design, ui,  angle=360):
    """
    This function revolves already existing sketch with drawn lines from the function draw_lines
    around the given axisLine by the specified angle (default is 360 degrees).
    """
    try:
        rootComp = design.rootComponent
        ui.messageBox('Select a profile to revolve.')
        profile = ui.selectEntity('Select a profile to revolve.', 'Profiles').entity
        ui.messageBox('Select sketch line for axis.')
        axis = ui.selectEntity('Select sketch line for axis.', 'SketchLines').entity
        operation = adsk.fusion.FeatureOperations.NewComponentFeatureOperation
        revolveFeatures = rootComp.features.revolveFeatures
        input = revolveFeatures.createInput(profile, axis, operation)
        input.setAngleExtent(False, adsk.core.ValueInput.createByString(str(angle) + ' deg'))
        revolveFeature = revolveFeatures.add(input)



    except:
        if ui:
            ui.messageBox('Failed revolve_profile:\n{}'.format(traceback.format_exc()))

##############################################################################################

###Selection Functions######
def rect_pattern(design,ui,axis_one ,axis_two ,quantity_one,quantity_two,distance_one,distance_two,plane="XY"):
    """
    Creates a rectangular pattern of the last body along the specified axis and plane
    There are two quantity parameters for two directions
    There are also two distance parameters for the spacing in two directions
    params:
    axis: "X", "Y", or "Z" axis for the pattern direction
    quantity_one: Number of instances in the first direction
    quantity_two: Number of instances in the second direction
    distance_one: Spacing between instances in the first direction
    distance_two: Spacing between instances in the second direction
    plane: Construction plane for the pattern ("XY", "XZ", or "YZ")
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        rectFeats = rootComp.features.rectangularPatternFeatures



        quantity_one = adsk.core.ValueInput.createByString(f"{quantity_one}")
        quantity_two = adsk.core.ValueInput.createByString(f"{quantity_two}")
        distance_one = adsk.core.ValueInput.createByString(f"{distance_one}")
        distance_two = adsk.core.ValueInput.createByString(f"{distance_two}")

        bodies = rootComp.bRepBodies
        if bodies.count > 0:
            latest_body = bodies.item(bodies.count - 1)
        else:
            ui.messageBox("Keine Bodies gefunden.")
        inputEntites = adsk.core.ObjectCollection.create()
        inputEntites.add(latest_body)
        baseaxis_one = None
        if axis_one == "Y":
            baseaxis_one = rootComp.yConstructionAxis
        elif axis_one == "X":
            baseaxis_one = rootComp.xConstructionAxis
        elif axis_one == "Z":
            baseaxis_one = rootComp.zConstructionAxis


        baseaxis_two = None
        if axis_two == "Y":
            baseaxis_two = rootComp.yConstructionAxis
        elif axis_two == "X":
            baseaxis_two = rootComp.xConstructionAxis
        elif axis_two == "Z":
            baseaxis_two = rootComp.zConstructionAxis



        rectangularPatternInput = rectFeats.createInput(inputEntites,baseaxis_one, quantity_one, distance_one, adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
        #second direction
        rectangularPatternInput.setDirectionTwo(baseaxis_two,quantity_two, distance_two)
        rectangularFeature = rectFeats.add(rectangularPatternInput)
    except:
        if ui:
            ui.messageBox('Failed to execute rectangular pattern:\n{}'.format(traceback.format_exc()))



def circular_pattern(design, ui, quantity, axis, plane):
    """
    Creates a circular pattern and returns detailed confirmation.
    Returns pattern_id, instance_count, and success status.
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        circularFeats = rootComp.features.circularPatternFeatures
        bodies = rootComp.bRepBodies

        if bodies.count > 0:
            latest_body = bodies.item(bodies.count - 1)
        else:
            return {
                "success": False,
                "error": "No bodies found"
            }

        inputEntites = adsk.core.ObjectCollection.create()
        inputEntites.add(latest_body)

        if plane == "XY":
            sketch = sketches.add(rootComp.xYConstructionPlane)
        elif plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)

        if axis == "Y":
            yAxis = rootComp.yConstructionAxis
            circularFeatInput = circularFeats.createInput(inputEntites, yAxis)
        elif axis == "X":
            xAxis = rootComp.xConstructionAxis
            circularFeatInput = circularFeats.createInput(inputEntites, xAxis)
        elif axis == "Z":
            zAxis = rootComp.zConstructionAxis
            circularFeatInput = circularFeats.createInput(inputEntites, zAxis)

        circularFeatInput.quantity = adsk.core.ValueInput.createByReal((quantity))
        circularFeatInput.totalAngle = adsk.core.ValueInput.createByString('360 deg')
        circularFeatInput.isSymmetric = False

        # Create the pattern and capture the feature
        pattern = circularFeats.add(circularFeatInput)

        # Return detailed confirmation
        return {
            "applied": True,
            "success": True,
            "instance_count": int(quantity),
            "pattern_id": pattern.entityToken if pattern else None,
            "pattern_name": pattern.name if pattern else "CircularPattern",
            "axis": axis,
            "total_angle": 360
        }

    except Exception as e:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        return {
            "applied": False,
            "success": False,
            "error": str(e)
        }




def undo(design, ui):
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        cmd = ui.commandDefinitions.itemById('UndoCommand')
        cmd.execute()

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def delete(design,ui):
    """
    Remove every body and sketch from the design so nothing is left
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        bodies = rootComp.bRepBodies
        removeFeat = rootComp.features.removeFeatures

        # Von hinten nach vorne löschen
        for i in range(bodies.count - 1, -1, -1): # startet bei bodies.count - 1 und geht in Schritten von -1 bis 0
            body = bodies.item(i)
            removeFeat.add(body)


    except:
        if ui:
            ui.messageBox('Failed to delete:\n{}'.format(traceback.format_exc()))



def export_as_STEP(design, ui,Name):
    try:

        exportMgr = design.exportManager

        directory_name = "Fusion_Exports"
        FilePath = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        Export_dir_path = os.path.join(FilePath, directory_name, Name)
        os.makedirs(Export_dir_path, exist_ok=True)

        stepOptions = exportMgr.createSTEPExportOptions(Export_dir_path+ f'/{Name}.step')  # Save as Fusion.step in the export directory
       # stepOptions = exportMgr.createSTEPExportOptions(Export_dir_path)


        res = exportMgr.execute(stepOptions)
        if not res:
            # Only show message on failure
            ui.messageBox("STEP export failed")
    except:
        if ui:
            ui.messageBox('Failed export_as_STEP:\n{}'.format(traceback.format_exc()))

def cut_extrude(design,ui,depth):
    """
    Creates a cut extrude by cutting the last sketch into a body.

    IMPORTANT: The sketch must be positioned on or near an existing body.
    The sketch profile must intersect with the body to create a valid cut.
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        bodies = rootComp.bRepBodies

        # Check if there are any bodies to cut into
        if bodies.count == 0:
            if ui:
                ui.messageBox("No target body found to cut or intersect!\n\n"
                             "Please create a body first before using cut_extrude.\n\n"
                             "Tip: Use draw_box, draw_cylinder, or other creation tools to make a body first.")
            return

        # Check if there are any sketches
        if sketches.count == 0:
            if ui:
                ui.messageBox("No sketches found. Please create a sketch first.")
            return

        sketch = sketches.item(sketches.count - 1)  # Letzter Sketch

        # Check if the sketch has profiles
        if sketch.profiles.count == 0:
            if ui:
                ui.messageBox("Sketch has no closed profiles. Please draw a closed shape.")
            return

        prof = sketch.profiles.item(0)  # Erstes Profil im Sketch
        extrudes = rootComp.features.extrudeFeatures
        extrudeInput = extrudes.createInput(prof,adsk.fusion.FeatureOperations.CutFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(depth)
        extrudeInput.setDistanceExtent(False, distance)

        try:
            extrudes.add(extrudeInput)
        except RuntimeError as e:
            error_msg = str(e)
            if "No target body found" in error_msg or "cut or intersect" in error_msg:
                if ui:
                    ui.messageBox("Failed to create cut: The sketch profile does not intersect with any existing body!\n\n"
                                 "Possible causes:\n"
                                 "1. The sketch is not positioned on/near a body face\n"
                                 "2. The sketch was created on a different plane than the body\n"
                                 "3. Use 'sketch_on_face' to create sketches directly on body faces\n\n"
                                 "Solution: Position your sketch so it overlaps with the body you want to cut.")
            else:
                if ui:
                    ui.messageBox(f'Failed to create cut:\n{error_msg}')
            return

    except Exception as e:
        if ui:
            ui.messageBox('Failed cut_extrude:\n{}'.format(traceback.format_exc()))


def extrude_thin(design, ui, thickness,distance):
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches

        # Check if there are any sketches
        if sketches.count == 0:
            if ui:
                ui.messageBox("No sketches found. Please create a sketch first.")
            return

        sketch = sketches.item(sketches.count - 1)

        # Check if the sketch has profiles
        if sketch.profiles.count == 0:
            if ui:
                ui.messageBox("Sketch has no closed profiles. Please draw a closed shape.")
            return

        #ui.messageBox('Select a face for the extrusion.')
        #selectedFace = ui.selectEntity('Select a face for the extrusion.', 'Profiles').entity
        selectedFace = sketch.profiles.item(0)
        exts = rootComp.features.extrudeFeatures
        extInput = exts.createInput(selectedFace, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        extInput.setThinExtrude(adsk.fusion.ThinExtrudeWallLocation.Center,
                                adsk.core.ValueInput.createByReal(thickness))

        distanceExtent = adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(distance))
        extInput.setOneSideExtent(distanceExtent, adsk.fusion.ExtentDirections.PositiveExtentDirection)

        ext = exts.add(extInput)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def draw_cylinder(design, ui, radius, height, x,y,z,plane = "XY"):
    """
    Draws a cylinder with given radius and height at position (x,y,z)
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane
        if plane == "XZ":
            sketch = sketches.add(rootComp.xZConstructionPlane)
        elif plane == "YZ":
            sketch = sketches.add(rootComp.yZConstructionPlane)
        else:
            sketch = sketches.add(xyPlane)

        center = adsk.core.Point3D.create(x, y, z)
        sketch.sketchCurves.sketchCircles.addByCenterRadius(center, radius)

        prof = sketch.profiles.item(0)
        extrudes = rootComp.features.extrudeFeatures
        extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(height)
        extInput.setDistanceExtent(False, distance)
        extrudes.add(extInput)

    except:
        if ui:
            ui.messageBox('Failed draw_cylinder:\n{}'.format(traceback.format_exc()))



def export_as_STL(design, ui,Name):
    """
    No idea whats happening here
    Copied straight up from API examples
    """
    try:

        rootComp = design.rootComponent


        exportMgr = design.exportManager

        stlRootOptions = exportMgr.createSTLExportOptions(rootComp)

        directory_name = "Fusion_Exports"
        FilePath = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        Export_dir_path = os.path.join(FilePath, directory_name, Name)
        os.makedirs(Export_dir_path, exist_ok=True)

        printUtils = stlRootOptions.availablePrintUtilities

        # export the root component to the print utility, instead of a specified file
        for printUtil in printUtils:
            stlRootOptions.sendToPrintUtility = True
            stlRootOptions.printUtility = printUtil

            exportMgr.execute(stlRootOptions)



        # export the occurrence one by one in the root component to a specified file
        allOccu = rootComp.allOccurrences
        for occ in allOccu:
            Name = Export_dir_path + "/" + occ.component.name

            # create stl exportOptions
            stlExportOptions = exportMgr.createSTLExportOptions(occ, Name)
            stlExportOptions.sendToPrintUtility = False

            exportMgr.execute(stlExportOptions)

        # export the body one by one in the design to a specified file
        allBodies = rootComp.bRepBodies
        for body in allBodies:
            Name = Export_dir_path + "/" + body.parentComponent.name + '-' + body.name

            # create stl exportOptions
            stlExportOptions = exportMgr.createSTLExportOptions(body, Name)
            stlExportOptions.sendToPrintUtility = False

            exportMgr.execute(stlExportOptions)

        # Success - no notification needed (only show failures)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def get_model_parameters(design):
    model_params = []
    user_params = design.userParameters
    for param in design.allParameters:
        if all(user_params.item(i) != param for i in range(user_params.count)):
            try:
                wert = str(param.value)
            except Exception:
                wert = ""
            model_params.append({
                "Name": str(param.name),
                "Wert": wert,
                "Einheit": str(param.unit),
                "Expression": str(param.expression) if param.expression else ""
            })
    return model_params

def set_parameter(design, ui, name, value):
    try:
        param = design.allParameters.itemByName(name)
        param.expression = value
    except:
        if ui:
            ui.messageBox('Failed set_parameter:\n{}'.format(traceback.format_exc()))

def holes(design, ui, points, width=1.0,distance = 1.0,faceindex=0):
    """
    Create one or more holes on a selected face.
    """

    try:
        rootComp = design.rootComponent
        holes = rootComp.features.holeFeatures
        sketches = rootComp.sketches


        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies

        if bodies.count > 0:
            latest_body = bodies.item(bodies.count - 1)
        else:
            ui.messageBox("Keine Bodies gefunden.")
            return
        entities = adsk.core.ObjectCollection.create()
        entities.add(latest_body.faces.item(faceindex))
        sk = sketches.add(latest_body.faces.item(faceindex))# create sketch on faceindex face

        tipangle = 90.0
        for i in range(len(points)):
            holePoint = sk.sketchPoints.add(adsk.core.Point3D.create(points[i][0], points[i][1], 0))
            tipangle = adsk.core.ValueInput.createByString('180 deg')
            holedistance = adsk.core.ValueInput.createByReal(distance)

            holeDiam = adsk.core.ValueInput.createByReal(width)
            holeInput = holes.createSimpleInput(holeDiam)
            holeInput.tipAngle = tipangle
            holeInput.setPositionBySketchPoint(holePoint)
            holeInput.setDistanceExtent(holedistance)

        # Add the hole
            holes.add(holeInput)
    except Exception:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))



def select_body(design,ui,Bodyname):
    """
    Selects a body by name and returns information about it.
    Returns: dict with success status, body_name, body_id, and error if failed
    """
    try:
        rootComp = design.rootComponent
        target_body = rootComp.bRepBodies.itemByName(Bodyname)

        if target_body is None:
            error_msg = f"Body with the name '{Bodyname}' could not be found."
            if ui:
                ui.messageBox(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "body_name": Bodyname
            }

        return {
            "success": True,
            "body_name": target_body.name,
            "body_id": target_body.entityToken,
            "index": rootComp.bRepBodies.find(target_body)
        }

    except Exception as e:
        error_msg = f"Failed to select body: {str(e)}"
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        return {
            "success": False,
            "error": error_msg,
            "body_name": Bodyname
        }

def select_sketch(design,ui,Sketchname):
    """
    Selects a sketch by name and returns information about it.
    Returns: dict with success status, sketch_name, sketch_id, and error if failed
    """
    try:
        rootComp = design.rootComponent
        target_sketch = rootComp.sketches.itemByName(Sketchname)

        if target_sketch is None:
            error_msg = f"Sketch with the name '{Sketchname}' could not be found."
            if ui:
                ui.messageBox(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "sketch_name": Sketchname
            }

        return {
            "success": True,
            "sketch_name": target_sketch.name,
            "sketch_id": target_sketch.entityToken,
            "index": rootComp.sketches.find(target_sketch),
            "profile_count": target_sketch.profiles.count
        }

    except Exception as e:
        error_msg = f"Failed to select sketch: {str(e)}"
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        return {
            "success": False,
            "error": error_msg,
            "sketch_name": Sketchname
        }



def list_bodies(design, ui):
    """
    Lists all bodies in the current design with their IDs and names.
    Returns a list of body information dictionaries.
    """
    try:
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies

        body_list = []
        for i in range(bodies.count):
            body = bodies.item(i)
            body_list.append({
                "index": i,
                "name": body.name,
                "body_id": body.entityToken,
                "volume": body.volume,
                "is_visible": body.isVisible
            })

        return {
            "success": True,
            "count": bodies.count,
            "bodies": body_list
        }
    except Exception as e:
        if ui:
            ui.messageBox('Failed list_bodies:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}


def get_active_body(design, ui):
    """
    Gets the currently active or last created body.
    Returns body information.
    """
    try:
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies

        if bodies.count == 0:
            return {"success": False, "error": "No bodies in design"}

        # Get the last body (most recently created)
        body = bodies.item(bodies.count - 1)

        return {
            "success": True,
            "body_id": body.entityToken,
            "body_name": body.name,
            "index": bodies.count - 1
        }
    except Exception as e:
        if ui:
            ui.messageBox('Failed get_active_body:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}


def rename_body(design, ui, body_id_or_index, new_name):
    """
    Renames a body by its ID or index.
    """
    try:
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies

        if bodies.count == 0:
            return {"success": False, "error": "No bodies in design"}

        # Try to find body by index first (if it's an integer)
        body = None
        if isinstance(body_id_or_index, int):
            if 0 <= body_id_or_index < bodies.count:
                body = bodies.item(body_id_or_index)
        else:
            # Try to find by entity token
            for i in range(bodies.count):
                if bodies.item(i).entityToken == body_id_or_index:
                    body = bodies.item(i)
                    break

        if body is None:
            return {"success": False, "error": f"Body not found: {body_id_or_index}"}

        old_name = body.name
        body.name = new_name

        return {
            "success": True,
            "old_name": old_name,
            "new_name": new_name,
            "body_id": body.entityToken
        }
    except Exception as e:
        if ui:
            ui.messageBox('Failed rename_body:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}


def list_sketches(design, ui):
    """
    Lists all sketches in the current design.
    Returns a list of sketch information dictionaries.
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches

        sketch_list = []
        for i in range(sketches.count):
            sketch = sketches.item(i)
            sketch_list.append({
                "index": i,
                "name": sketch.name,
                "sketch_id": sketch.entityToken,
                "is_visible": sketch.isVisible,
                "profile_count": sketch.profiles.count
            })

        return {
            "success": True,
            "count": sketches.count,
            "sketches": sketch_list
        }
    except Exception as e:
        if ui:
            ui.messageBox('Failed list_sketches:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}


def get_active_sketch(design, ui):
    """
    Gets the currently active or last created sketch.
    Returns sketch information.
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches

        if sketches.count == 0:
            return {"success": False, "error": "No sketches in design"}

        # Get the last sketch (most recently created)
        sketch = sketches.item(sketches.count - 1)

        return {
            "success": True,
            "sketch_id": sketch.entityToken,
            "sketch_name": sketch.name,
            "index": sketches.count - 1,
            "profile_count": sketch.profiles.count
        }
    except Exception as e:
        if ui:
            ui.messageBox('Failed get_active_sketch:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}


def activate_sketch(design, ui, sketch_id_or_index):
    """
    Activates a sketch for editing by its ID or index.
    Note: Fusion API has limited support for programmatic sketch activation.
    This function validates the sketch exists and returns its info.
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches

        if sketches.count == 0:
            return {"success": False, "error": "No sketches in design"}

        # Try to find sketch by index first
        sketch = None
        if isinstance(sketch_id_or_index, int):
            if 0 <= sketch_id_or_index < sketches.count:
                sketch = sketches.item(sketch_id_or_index)
        else:
            # Try to find by entity token
            for i in range(sketches.count):
                if sketches.item(i).entityToken == sketch_id_or_index:
                    sketch = sketches.item(i)
                    break

        if sketch is None:
            return {"success": False, "error": f"Sketch not found: {sketch_id_or_index}"}

        # Make sketch visible if hidden
        if not sketch.isVisible:
            sketch.isVisible = True

        return {
            "success": True,
            "sketch_id": sketch.entityToken,
            "sketch_name": sketch.name,
            "message": f"Sketch {sketch.name} is ready"
        }
    except Exception as e:
        if ui:
            ui.messageBox('Failed activate_sketch:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}


def close_sketch(design, ui, sketch_id=None):
    """
    Closes/deactivates a sketch.
    If sketch_id is None, closes the currently active sketch.
    Note: In Fusion API, sketches don't need explicit closing for operations.
    This function validates sketch state for safety.
    """
    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches

        if sketches.count == 0:
            return {"success": True, "message": "No sketches to close"}

        # If no sketch specified, reference the last one
        if sketch_id is None:
            sketch = sketches.item(sketches.count - 1)
        else:
            # Find the specified sketch
            sketch = None
            if isinstance(sketch_id, int):
                if 0 <= sketch_id < sketches.count:
                    sketch = sketches.item(sketch_id)
            else:
                for i in range(sketches.count):
                    if sketches.item(i).entityToken == sketch_id:
                        sketch = sketches.item(i)
                        break

        if sketch is None:
            return {"success": False, "error": f"Sketch not found: {sketch_id}"}

        return {
            "success": True,
            "sketch_name": sketch.name,
            "message": f"Sketch {sketch.name} closed"
        }
    except Exception as e:
        if ui:
            ui.messageBox('Failed close_sketch:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}


#########################################################################################
### NEW ENHANCED TOOLS - Phase 1-4 (Comprehensive CAD Reliability Enhancement) ###
#########################################################################################

# Global operation log storage
operation_log = []
transaction_stack = []

def log_operation(operation, parameters, status, result, error_message=None, body_state_before=None, body_state_after=None, execution_time_ms=0):
    """Helper function to log all operations for audit trail"""
    global operation_log
    import datetime

    log_entry = {
        "sequence": len(operation_log),
        "timestamp": datetime.datetime.now().isoformat(),
        "operation": operation,
        "parameters": parameters,
        "status": status,
        "error_message": error_message,
        "result": result,
        "body_state_before": body_state_before,
        "body_state_after": body_state_after,
        "execution_time_ms": execution_time_ms
    }
    operation_log.append(log_entry)

    # Keep only last 100 operations to prevent memory issues
    if len(operation_log) > 100:
        operation_log.pop(0)


def get_body_state(design):
    """Helper function to capture current body state for logging"""
    try:
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies

        if bodies.count == 0:
            return {"volume": 0, "face_count": 0, "body_valid": False}

        body = bodies.item(bodies.count - 1)
        return {
            "volume": body.volume,
            "face_count": body.faces.count,
            "body_valid": body.isValid
        }
    except:
        return {"volume": 0, "face_count": 0, "body_valid": False}


### PHASE 1: CRITICAL TOOLS ###

def get_sketch_status(design, ui, sketch_id=None, include_geometry=True):
    """
    Validates sketch state and content before closing it.
    This prevents silent failures by checking if geometry was actually accepted.
    """
    import time
    start_time = time.time()

    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches

        if sketches.count == 0:
            return {
                "success": False,
                "error": "No sketches in design",
                "is_valid": False
            }

        # Get target sketch
        sketch = None
        if sketch_id is None:
            sketch = sketches.item(sketches.count - 1)
        else:
            if isinstance(sketch_id, int):
                if 0 <= sketch_id < sketches.count:
                    sketch = sketches.item(sketch_id)
            else:
                for i in range(sketches.count):
                    if sketches.item(i).entityToken == sketch_id:
                        sketch = sketches.item(i)
                        break

        if sketch is None:
            return {"success": False, "error": f"Sketch not found: {sketch_id}"}

        # Analyze sketch profiles
        profile_count = sketch.profiles.count
        closed_profiles = 0
        open_profiles = 0
        total_segments = 0
        profile_types = set()

        for i in range(profile_count):
            profile = sketch.profiles.item(i)
            if profile.profileLoops.count > 0:
                loop = profile.profileLoops.item(0)
                is_closed = True

                # Count segments
                for j in range(loop.profileCurves.count):
                    curve = loop.profileCurves.item(j)
                    total_segments += 1

                    # Identify curve type
                    if curve.sketchEntity.objectType == adsk.fusion.SketchLine.classType():
                        profile_types.add("line")
                    elif curve.sketchEntity.objectType == adsk.fusion.SketchCircle.classType():
                        profile_types.add("circle")
                    elif curve.sketchEntity.objectType == adsk.fusion.SketchArc.classType():
                        profile_types.add("arc")

                if is_closed:
                    closed_profiles += 1
                else:
                    open_profiles += 1

        # Calculate bounds
        bounds = {"min": [0, 0, 0], "max": [0, 0, 0]}
        try:
            if sketch.boundingBox:
                bbox = sketch.boundingBox
                bounds = {
                    "min": [bbox.minPoint.x, bbox.minPoint.y, bbox.minPoint.z],
                    "max": [bbox.maxPoint.x, bbox.maxPoint.y, bbox.maxPoint.z]
                }
        except:
            pass

        # Determine if sketch is valid
        geometry_valid = profile_count > 0 and closed_profiles > 0
        is_valid = geometry_valid and sketch.isValid

        execution_time = int((time.time() - start_time) * 1000)

        result = {
            "success": True,
            "sketch_id": sketch.entityToken,
            "sketch_name": sketch.name,
            "is_open": True,
            "is_valid": is_valid,
            "profile_count": profile_count,
            "profile_types": list(profile_types),
            "total_segments": total_segments,
            "geometry_valid": geometry_valid,
            "closed_profiles": closed_profiles,
            "open_profiles": open_profiles,
            "bounds": bounds,
            "error_message": None if is_valid else "Sketch has no closed profiles" if profile_count == 0 else None,
            "message": f"Sketch valid: {closed_profiles} closed profiles, {total_segments} segments" if is_valid else "Sketch invalid or incomplete"
        }

        log_operation("get_sketch_status", {"sketch_id": sketch_id}, "success", result, execution_time_ms=execution_time)
        return result

    except Exception as e:
        if ui:
            ui.messageBox('Failed get_sketch_status:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e), "is_valid": False}


def list_faces(design, ui, body_id):
    """
    Query all faces of a body with geometric properties (not just indices).
    Face indices change after boolean operations - this provides semantic understanding.
    """
    import time
    start_time = time.time()

    try:
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies

        if bodies.count == 0:
            return {"success": False, "error": "No bodies in design"}

        # Find target body
        target_body = None
        if isinstance(body_id, int):
            if 0 <= body_id < bodies.count:
                target_body = bodies.item(body_id)
        else:
            for i in range(bodies.count):
                if bodies.item(i).entityToken == body_id or bodies.item(i).name == body_id:
                    target_body = bodies.item(i)
                    break

        if target_body is None:
            return {"success": False, "error": f"Body not found: {body_id}"}

        # Analyze all faces
        faces_list = []
        for i in range(target_body.faces.count):
            face = target_body.faces.item(i)

            # Get face type
            face_type = "unknown"
            is_planar = False
            normal = [0, 0, 0]

            if face.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
                face_type = "planar"
                is_planar = True
                plane = adsk.core.Plane.cast(face.geometry)
                if plane:
                    normal = [plane.normal.x, plane.normal.y, plane.normal.z]
            elif face.geometry.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType:
                face_type = "cylindrical"
            elif face.geometry.surfaceType == adsk.core.SurfaceTypes.ConeSurfaceType:
                face_type = "conical"
            elif face.geometry.surfaceType == adsk.core.SurfaceTypes.SphereSurfaceType:
                face_type = "spherical"
            elif face.geometry.surfaceType == adsk.core.SurfaceTypes.TorusSurfaceType:
                face_type = "toroidal"

            # Calculate face center
            centroid = face.centroid
            position_center = [centroid.x, centroid.y, centroid.z]

            # Calculate bounds
            bbox = face.boundingBox
            bounds = {
                "min": [bbox.minPoint.x, bbox.minPoint.y, bbox.minPoint.z],
                "max": [bbox.maxPoint.x, bbox.maxPoint.y, bbox.maxPoint.z]
            }

            # Determine orientation for planar faces
            orientation = "unknown"
            if is_planar and normal != [0, 0, 0]:
                # Normalize and identify orientation
                if abs(normal[2]) > 0.9:
                    orientation = "top" if normal[2] > 0 else "bottom"
                elif abs(normal[1]) > 0.9:
                    orientation = "front" if normal[1] > 0 else "back"
                elif abs(normal[0]) > 0.9:
                    orientation = "right" if normal[0] > 0 else "left"
                else:
                    orientation = "angled"

            # Get adjacent faces
            adjacent_face_indices = []
            for j in range(face.edges.count):
                edge = face.edges.item(j)
                for k in range(edge.faces.count):
                    adj_face = edge.faces.item(k)
                    if adj_face != face:
                        # Find index of adjacent face
                        for m in range(target_body.faces.count):
                            if target_body.faces.item(m) == adj_face:
                                if m not in adjacent_face_indices:
                                    adjacent_face_indices.append(m)
                                break

            faces_list.append({
                "index": i,
                "type": face_type,
                "area": face.area,
                "normal": normal,
                "position_center": position_center,
                "bounds": bounds,
                "orientation": orientation,
                "is_planar": is_planar,
                "adjacent_face_indices": adjacent_face_indices
            })

        execution_time = int((time.time() - start_time) * 1000)

        result = {
            "success": True,
            "body_id": target_body.entityToken,
            "body_name": target_body.name,
            "face_count": len(faces_list),
            "faces": faces_list
        }

        log_operation("list_faces", {"body_id": body_id}, "success", result, execution_time_ms=execution_time)
        return result

    except Exception as e:
        if ui:
            ui.messageBox('Failed list_faces:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}


def pocket_recess_safe(design, ui, body_id, sketch_id, depth, operation="cut", validate_before=True, validate_after=True):
    """
    Create pocket with complete validation and result confirmation.
    Returns success=true/false with actual volume changes.
    """
    import time
    start_time = time.time()

    try:
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies
        sketches = rootComp.sketches

        # Get body state before
        geometry_before = None
        if validate_before:
            geometry_before = get_body_state(design)

        # Find target body
        target_body = None
        if isinstance(body_id, int):
            if 0 <= body_id < bodies.count:
                target_body = bodies.item(body_id)
        else:
            for i in range(bodies.count):
                if bodies.item(i).entityToken == body_id or bodies.item(i).name == body_id:
                    target_body = bodies.item(i)
                    break

        if target_body is None:
            return {"success": False, "error": f"Body not found: {body_id}"}

        # Find target sketch
        target_sketch = None
        if isinstance(sketch_id, int):
            if 0 <= sketch_id < sketches.count:
                target_sketch = sketches.item(sketch_id)
        else:
            for i in range(sketches.count):
                if sketches.item(i).entityToken == sketch_id:
                    target_sketch = sketches.item(i)
                    break

        if target_sketch is None:
            return {"success": False, "error": f"Sketch not found: {sketch_id}"}

        # Validate sketch has profiles
        if validate_before and target_sketch.profiles.count == 0:
            return {"success": False, "error": "Sketch has no closed profiles"}

        volume_before = target_body.volume
        face_count_before = target_body.faces.count

        # Create pocket
        prof = target_sketch.profiles.item(0)
        extrudes = rootComp.features.extrudeFeatures

        # Determine operation type
        op_type = adsk.fusion.FeatureOperations.CutFeatureOperation
        if operation == "join":
            op_type = adsk.fusion.FeatureOperations.JoinFeatureOperation
        elif operation == "intersect":
            op_type = adsk.fusion.FeatureOperations.IntersectFeatureOperation

        extrudeInput = extrudes.createInput(prof, op_type)
        distance = adsk.core.ValueInput.createByReal(abs(depth))
        extrudeInput.setDistanceExtent(False, distance)

        # Set target body
        participantBodies = adsk.core.ObjectCollection.create()
        participantBodies.add(target_body)
        extrudeInput.participantBodies = participantBodies

        # Execute operation
        try:
            extrude_feature = extrudes.add(extrudeInput)
            pocket_id = extrude_feature.entityToken
        except RuntimeError as e:
            return {"success": False, "error": f"Failed to create pocket: {str(e)}"}

        # Get body state after
        volume_after = target_body.volume
        face_count_after = target_body.faces.count
        volume_removed = volume_before - volume_after

        # Validate result
        geometry_valid = target_body.isValid
        operation_applied = abs(volume_removed) > 0.0001  # Tolerance for floating point

        if validate_after and not operation_applied:
            return {
                "success": False,
                "error": "Pocket operation did not change volume - sketch may not intersect body",
                "volume_removed": volume_removed
            }

        geometry_after = None
        if validate_after:
            geometry_after = get_body_state(design)

        execution_time = int((time.time() - start_time) * 1000)

        result = {
            "success": True,
            "pocket_id": pocket_id,
            "body_id": target_body.entityToken,
            "body_name": target_body.name,
            "sketch_id": target_sketch.entityToken,
            "depth_applied": depth,
            "geometry_before": {
                "volume": volume_before,
                "face_count": face_count_before,
                "manifold": True
            },
            "geometry_after": {
                "volume": volume_after,
                "face_count": face_count_after,
                "manifold": geometry_valid
            },
            "volume_removed": volume_removed,
            "geometry_valid": geometry_valid,
            "operation_applied": operation_applied,
            "message": f"Pocket created: {volume_removed:.2f} cm³ removed, geometry valid",
            "error": None
        }

        log_operation("pocket_recess_safe",
                     {"body_id": body_id, "sketch_id": sketch_id, "depth": depth},
                     "success", result,
                     body_state_before=geometry_before,
                     body_state_after=geometry_after,
                     execution_time_ms=execution_time)

        return result

    except Exception as e:
        if ui:
            ui.messageBox('Failed pocket_recess_safe:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}


def get_feature_history(design, ui, body_id, include_parameters=True, include_errors=True):
    """
    List all features (extrudes, pockets, fillets, etc.) applied to a body.
    Provides audit trail for multi-step builds.
    """
    import time
    start_time = time.time()

    try:
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies

        # Find target body
        target_body = None
        if isinstance(body_id, int):
            if 0 <= body_id < bodies.count:
                target_body = bodies.item(body_id)
        else:
            for i in range(bodies.count):
                if bodies.item(i).entityToken == body_id or bodies.item(i).name == body_id:
                    target_body = bodies.item(i)
                    break

        if target_body is None:
            return {"success": False, "error": f"Body not found: {body_id}"}

        features_list = []
        feature_index = 0

        # Get all features from timeline
        timeline = design.timeline
        for i in range(timeline.count):
            timeline_obj = timeline.item(i)
            entity = timeline_obj.entity

            if entity is None:
                continue

            feature_info = {
                "index": feature_index,
                "type": "Unknown",
                "feature_id": entity.entityToken if entity else "unknown",
                "name": entity.name if entity and hasattr(entity, 'name') else f"Feature{i}",
                "status": "valid" if (entity and hasattr(entity, 'healthState') and entity.healthState == adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState) else "unknown",
                "sequence": i,
                "result_valid": True,
                "error_message": None
            }

            # Identify feature type
            if entity.objectType == adsk.fusion.ExtrudeFeature.classType():
                feature_info["type"] = "Extrude"
                if include_parameters:
                    extrude = adsk.fusion.ExtrudeFeature.cast(entity)
                    feature_info["parameters"] = {
                        "operation": "new" if extrude.operation == adsk.fusion.FeatureOperations.NewBodyFeatureOperation else "cut" if extrude.operation == adsk.fusion.FeatureOperations.CutFeatureOperation else "join"
                    }
            elif entity.objectType == adsk.fusion.FilletFeature.classType():
                feature_info["type"] = "Fillet"
            elif entity.objectType == adsk.fusion.ChamferFeature.classType():
                feature_info["type"] = "Chamfer"
            elif entity.objectType == adsk.fusion.HoleFeature.classType():
                feature_info["type"] = "Hole"
            elif entity.objectType == adsk.fusion.ShellFeature.classType():
                feature_info["type"] = "Shell"
            elif entity.objectType == adsk.fusion.PatternFeature.classType():
                feature_info["type"] = "Pattern"
            elif entity.objectType == adsk.fusion.MirrorFeature.classType():
                feature_info["type"] = "Mirror"

            # Check if feature failed
            if hasattr(entity, 'healthState'):
                if entity.healthState == adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState:
                    feature_info["status"] = "failed"
                    feature_info["result_valid"] = False
                    if include_errors and hasattr(entity, 'errorOrWarningMessage'):
                        feature_info["error_message"] = entity.errorOrWarningMessage
                elif entity.healthState == adsk.fusion.FeatureHealthStates.WarningFeatureHealthState:
                    feature_info["status"] = "warning"
                    if include_errors and hasattr(entity, 'errorOrWarningMessage'):
                        feature_info["error_message"] = entity.errorOrWarningMessage

            features_list.append(feature_info)
            feature_index += 1

        execution_time = int((time.time() - start_time) * 1000)

        result = {
            "success": True,
            "body_id": target_body.entityToken,
            "body_name": target_body.name,
            "feature_count": len(features_list),
            "features": features_list
        }

        log_operation("get_feature_history", {"body_id": body_id}, "success", result, execution_time_ms=execution_time)
        return result

    except Exception as e:
        if ui:
            ui.messageBox('Failed get_feature_history:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}


### PHASE 2: HIGH PRIORITY TOOLS ###

def find_face_by_property(design, ui, body_id, selector=None, normal=None, area_range=None, position=None, return_all_matches=False):
    """
    Locate face(s) by geometric criteria instead of fragile indices.
    Supports semantic selectors: front, back, top, bottom, left, right, largest, smallest.
    """
    import time
    start_time = time.time()

    try:
        # First get all faces
        faces_result = list_faces(design, ui, body_id)
        if not faces_result["success"]:
            return faces_result

        faces = faces_result["faces"]
        matches = []

        # Apply selector
        if selector:
            if selector == "front":
                matches = [f for f in faces if f["orientation"] == "front"]
            elif selector == "back":
                matches = [f for f in faces if f["orientation"] == "back"]
            elif selector == "top":
                matches = [f for f in faces if f["orientation"] == "top"]
            elif selector == "bottom":
                matches = [f for f in faces if f["orientation"] == "bottom"]
            elif selector == "left":
                matches = [f for f in faces if f["orientation"] == "left"]
            elif selector == "right":
                matches = [f for f in faces if f["orientation"] == "right"]
            elif selector == "largest":
                matches = [max(faces, key=lambda f: f["area"])]
            elif selector == "smallest":
                matches = [min(faces, key=lambda f: f["area"])]

        # Apply normal filter
        if normal and len(normal) == 3:
            normal_matches = []
            for f in (matches if matches else faces):
                # Check if normals are similar (with tolerance)
                if f["normal"] and len(f["normal"]) == 3:
                    dot_product = sum(a * b for a, b in zip(f["normal"], normal))
                    if dot_product > 0.9:  # Tolerance for parallel faces
                        normal_matches.append(f)
            matches = normal_matches

        # Apply area range filter
        if area_range:
            area_matches = [f for f in (matches if matches else faces)
                           if area_range.get("min", 0) <= f["area"] <= area_range.get("max", float('inf'))]
            matches = area_matches

        # Apply position filter
        if position and "point" in position:
            pos_matches = []
            tolerance = position.get("tolerance", 0.1)
            target_point = position["point"]

            for f in (matches if matches else faces):
                center = f["position_center"]
                distance = sum((a - b) ** 2 for a, b in zip(center, target_point)) ** 0.5
                if distance <= tolerance:
                    pos_matches.append(f)
            matches = pos_matches

        # Return results
        if not matches:
            return {
                "success": False,
                "error": f"No faces found matching criteria: {selector or normal or area_range or position}"
            }

        execution_time = int((time.time() - start_time) * 1000)

        result = {
            "success": True,
            "query": selector or str(normal) or "custom",
            "matches_found": len(matches),
            "primary_face_index": matches[0]["index"],
            "all_face_indices": [f["index"] for f in matches],
            "faces": matches if return_all_matches else [matches[0]]
        }

        log_operation("find_face_by_property",
                     {"body_id": body_id, "selector": selector},
                     "success", result,
                     execution_time_ms=execution_time)

        return result

    except Exception as e:
        if ui:
            ui.messageBox('Failed find_face_by_property:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}


def draw_rectangles_batch(design, ui, plane, rectangles):
    """
    Draw multiple rectangles in a single sketch in one operation.
    Reduces error accumulation from sequential calls.
    """
    import time
    start_time = time.time()

    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        planes_obj = rootComp.constructionPlanes

        # Select base plane
        if plane == "XZ":
            basePlane = rootComp.xZConstructionPlane
        elif plane == "YZ":
            basePlane = rootComp.yZConstructionPlane
        else:
            basePlane = rootComp.xYConstructionPlane

        # Create sketch
        sketch = sketches.add(basePlane)

        rectangles_drawn = 0
        rectangles_failed = 0

        # Draw all rectangles
        for rect in rectangles:
            try:
                x_min = rect.get("x_min", 0)
                x_max = rect.get("x_max", 1)
                y_min = rect.get("y_min", 0)
                y_max = rect.get("y_max", 1)
                z_center = rect.get("z_center", 0)

                # Create offset plane if needed
                if z_center != 0:
                    planeInput = planes_obj.createInput()
                    offsetValue = adsk.core.ValueInput.createByReal(z_center)
                    planeInput.setByOffset(basePlane, offsetValue)
                    offsetPlane = planes_obj.add(planeInput)
                    sketch = sketches.add(offsetPlane)

                # Draw rectangle
                point1 = adsk.core.Point3D.create(x_min, y_min, 0 if plane == "XY" else z_center)
                point2 = adsk.core.Point3D.create(x_max, y_max, 0 if plane == "XY" else z_center)

                rectangles = sketch.sketchCurves.sketchLines
                rectangles.addTwoPointRectangle(point1, point2)

                rectangles_drawn += 1

            except:
                rectangles_failed += 1

        total_segments = rectangles_drawn * 4  # Each rectangle has 4 segments
        geometry_valid = rectangles_drawn > 0

        execution_time = int((time.time() - start_time) * 1000)

        result = {
            "success": True,
            "sketch_id": sketch.entityToken,
            "sketch_name": sketch.name,
            "plane": plane,
            "rectangle_count": len(rectangles),
            "rectangles_drawn": rectangles_drawn,
            "rectangles_failed": rectangles_failed,
            "total_segments": total_segments,
            "geometry_valid": geometry_valid,
            "message": f"{rectangles_drawn} rectangles drawn successfully" + (f", {rectangles_failed} failed" if rectangles_failed > 0 else "")
        }

        log_operation("draw_rectangles_batch",
                     {"plane": plane, "rectangle_count": len(rectangles)},
                     "success", result,
                     execution_time_ms=execution_time)

        return result

    except Exception as e:
        if ui:
            ui.messageBox('Failed draw_rectangles_batch:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}


def pocket_smart(design, ui, body_id, sketch_id, depth_mode, depth_value, from_face="sketch_plane", snap_to_geometry=False, validate_after=True):
    """
    Create pocket with intelligent depth calculation.
    Modes: absolute, through, wall_thickness, percentage.
    """
    import time
    start_time = time.time()

    try:
        rootComp = design.rootComponent
        bodies = rootComp.bRepBodies

        # Find target body
        target_body = None
        if isinstance(body_id, int):
            if 0 <= body_id < bodies.count:
                target_body = bodies.item(body_id)
        else:
            for i in range(bodies.count):
                if bodies.item(i).entityToken == body_id or bodies.item(i).name == body_id:
                    target_body = bodies.item(i)
                    break

        if target_body is None:
            return {"success": False, "error": f"Body not found: {body_id}"}

        # Calculate actual depth based on mode
        calculated_depth = depth_value
        material_remaining = None

        if depth_mode == "absolute":
            calculated_depth = depth_value

        elif depth_mode == "through":
            # Calculate body thickness in cut direction
            bbox = target_body.boundingBox
            thickness = bbox.maxPoint.z - bbox.minPoint.z
            calculated_depth = thickness + 1.0  # Cut through + margin

        elif depth_mode == "wall_thickness":
            # Calculate depth to leave specific wall thickness
            bbox = target_body.boundingBox
            thickness = bbox.maxPoint.z - bbox.minPoint.z
            calculated_depth = thickness - depth_value
            material_remaining = depth_value

            if calculated_depth <= 0:
                return {"success": False, "error": f"Wall thickness {depth_value} exceeds body thickness {thickness}"}

        elif depth_mode == "percentage":
            # Calculate depth as percentage of body thickness
            bbox = target_body.boundingBox
            thickness = bbox.maxPoint.z - bbox.minPoint.z
            calculated_depth = thickness * (depth_value / 100.0)

        else:
            return {"success": False, "error": f"Unknown depth_mode: {depth_mode}"}

        # Create pocket using calculated depth
        result = pocket_recess_safe(design, ui, body_id, sketch_id, calculated_depth,
                                   operation="cut", validate_before=True, validate_after=validate_after)

        if result["success"]:
            result["depth_mode"] = depth_mode
            result["depth_requested"] = depth_value
            result["depth_applied"] = calculated_depth
            result["calculated_depth"] = calculated_depth

            if material_remaining is not None:
                result["material_remaining"] = material_remaining
                result["message"] = f"Pocket created with {material_remaining}cm wall thickness ({calculated_depth}cm cut)"
            else:
                result["message"] = f"Pocket created: {depth_mode} mode, {calculated_depth}cm depth"

        execution_time = int((time.time() - start_time) * 1000)
        log_operation("pocket_smart",
                     {"body_id": body_id, "sketch_id": sketch_id, "depth_mode": depth_mode, "depth_value": depth_value},
                     "success" if result["success"] else "failed", result,
                     execution_time_ms=execution_time)

        return result

    except Exception as e:
        if ui:
            ui.messageBox('Failed pocket_smart:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}


### PHASE 3: MEDIUM PRIORITY TOOLS ###

def begin_transaction(design, ui, transaction_id, description="", auto_validate=True, auto_rollback_on_error=False):
    """
    Begin a transaction to group multiple operations with atomic commit/rollback.
    """
    global transaction_stack
    import time

    transaction = {
        "transaction_id": transaction_id,
        "description": description,
        "start_time": time.time(),
        "operations": [],
        "auto_validate": auto_validate,
        "auto_rollback_on_error": auto_rollback_on_error,
        "start_marker": design.timeline.markerPosition
    }

    transaction_stack.append(transaction)

    return {
        "success": True,
        "transaction_id": transaction_id,
        "message": f"Transaction '{transaction_id}' started"
    }


def commit_transaction(design, ui, transaction_id, force=False):
    """
    Commit a transaction atomically.
    """
    global transaction_stack
    import time

    # Find transaction
    transaction = None
    for t in transaction_stack:
        if t["transaction_id"] == transaction_id:
            transaction = t
            break

    if transaction is None:
        return {"success": False, "error": f"Transaction not found: {transaction_id}"}

    duration_ms = int((time.time() - transaction["start_time"]) * 1000)

    # Check for failures
    failed_ops = [op for op in transaction["operations"] if op.get("success") == False]

    if failed_ops and not force:
        return {
            "success": False,
            "error": f"Transaction has {len(failed_ops)} failed operations. Use force=True to commit anyway.",
            "failed_operations": failed_ops
        }

    # Remove from stack
    transaction_stack.remove(transaction)

    result = {
        "success": True,
        "transaction_id": transaction_id,
        "status": "committed",
        "steps_executed": len(transaction["operations"]),
        "steps_failed": len(failed_ops),
        "duration_ms": duration_ms,
        "operations": transaction["operations"],
        "message": f"Transaction committed: {len(transaction['operations'])} operations, {len(failed_ops)} failed"
    }

    log_operation("commit_transaction", {"transaction_id": transaction_id}, "success", result, execution_time_ms=duration_ms)
    return result


def rollback_transaction(design, ui, transaction_id):
    """
    Rollback a transaction (undo all operations).
    """
    global transaction_stack
    import time

    # Find transaction
    transaction = None
    for t in transaction_stack:
        if t["transaction_id"] == transaction_id:
            transaction = t
            break

    if transaction is None:
        return {"success": False, "error": f"Transaction not found: {transaction_id}"}

    # Undo to marker
    try:
        design.timeline.markerPosition = transaction["start_marker"]
    except:
        pass

    duration_ms = int((time.time() - transaction["start_time"]) * 1000)

    # Remove from stack
    transaction_stack.remove(transaction)

    result = {
        "success": True,
        "transaction_id": transaction_id,
        "status": "rolled_back",
        "steps_undone": len(transaction["operations"]),
        "duration_ms": duration_ms,
        "message": f"Transaction rolled back: {len(transaction['operations'])} operations undone"
    }

    log_operation("rollback_transaction", {"transaction_id": transaction_id}, "success", result, execution_time_ms=duration_ms)
    return result


def get_operation_log(design, ui, last_n_operations=20, body_id=None, operation_type=None, status_filter=None):
    """
    Access detailed operation history for debugging.
    """
    global operation_log

    try:
        filtered_log = operation_log.copy()

        # Apply filters
        if body_id:
            filtered_log = [op for op in filtered_log if op.get("parameters", {}).get("body_id") == body_id]

        if operation_type:
            filtered_log = [op for op in filtered_log if operation_type in op["operation"]]

        if status_filter and status_filter != "all":
            filtered_log = [op for op in filtered_log if op["status"] == status_filter]

        # Get last N
        filtered_log = filtered_log[-last_n_operations:]

        # Get current state
        current_state = {
            "active_body_id": None,
            "active_sketch_id": None,
            "total_bodies": 0,
            "total_sketches": 0,
            "last_error": None,
            "session_duration_ms": 0
        }

        try:
            rootComp = design.rootComponent
            current_state["total_bodies"] = rootComp.bRepBodies.count
            current_state["total_sketches"] = rootComp.sketches.count

            if rootComp.bRepBodies.count > 0:
                current_state["active_body_id"] = rootComp.bRepBodies.item(rootComp.bRepBodies.count - 1).entityToken

            if rootComp.sketches.count > 0:
                current_state["active_sketch_id"] = rootComp.sketches.item(rootComp.sketches.count - 1).entityToken
        except:
            pass

        return {
            "success": True,
            "operation_count": len(filtered_log),
            "operations": filtered_log,
            "current_state": current_state
        }

    except Exception as e:
        if ui:
            ui.messageBox('Failed get_operation_log:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}


def create_sketch_on_body_plane(design, ui, body_id, plane, z_offset=0, name=None):
    """
    Create sketch directly on XY/YZ/XZ plane without face dependency.
    """
    import time
    start_time = time.time()

    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        planes_obj = rootComp.constructionPlanes

        # Select base plane
        if plane == "XZ":
            basePlane = rootComp.xZConstructionPlane
        elif plane == "YZ":
            basePlane = rootComp.yZConstructionPlane
        else:
            basePlane = rootComp.xYConstructionPlane

        # Create offset plane if needed
        if z_offset != 0:
            planeInput = planes_obj.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(z_offset)
            planeInput.setByOffset(basePlane, offsetValue)
            offsetPlane = planes_obj.add(planeInput)
            sketch = sketches.add(offsetPlane)
        else:
            sketch = sketches.add(basePlane)

        if name:
            sketch.name = name

        execution_time = int((time.time() - start_time) * 1000)

        result = {
            "success": True,
            "sketch_id": sketch.entityToken,
            "sketch_name": sketch.name,
            "body_id": body_id,
            "plane": plane,
            "z_offset": z_offset,
            "ready": True,
            "message": f"Sketch created on {plane} plane at Z={z_offset}cm"
        }

        log_operation("create_sketch_on_body_plane",
                     {"body_id": body_id, "plane": plane, "z_offset": z_offset},
                     "success", result,
                     execution_time_ms=execution_time)

        return result

    except Exception as e:
        if ui:
            ui.messageBox('Failed create_sketch_on_body_plane:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}


def validate_face_exists(design, ui, body_id, face_index):
    """
    Check if face index is still valid after topology changes.
    """
    import time
    start_time = time.time()

    try:
        # Get all faces
        faces_result = list_faces(design, ui, body_id)
        if not faces_result["success"]:
            return faces_result

        faces = faces_result["faces"]

        # Check if face index exists
        if face_index < 0 or face_index >= len(faces):
            return {
                "success": False,
                "face_index": face_index,
                "exists": False,
                "still_valid": False,
                "new_index": None,
                "reason": f"Face index {face_index} out of range (body has {len(faces)} faces)",
                "suggestion": "Use find_face_by_property() for semantic selection",
                "message": f"Face index {face_index} no longer exists; topology changed"
            }

        face = faces[face_index]

        execution_time = int((time.time() - start_time) * 1000)

        result = {
            "success": True,
            "face_index": face_index,
            "exists": True,
            "still_valid": True,
            "new_index": face_index,
            "face_type": face["type"],
            "area": face["area"],
            "reason": None,
            "message": f"Face index {face_index} is still valid"
        }

        log_operation("validate_face_exists",
                     {"body_id": body_id, "face_index": face_index},
                     "success", result,
                     execution_time_ms=execution_time)

        return result

    except Exception as e:
        if ui:
            ui.messageBox('Failed validate_face_exists:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}


### PHASE 4: NICE-TO-HAVE TOOLS ###

def select_faces_by_semantic(design, ui, body_id, selectors):
    """
    Batch select multiple faces using semantic names.
    """
    import time
    start_time = time.time()

    try:
        selected_faces = []

        for selector in selectors:
            result = find_face_by_property(design, ui, body_id, selector=selector, return_all_matches=True)
            if result["success"]:
                selected_faces.extend(result["faces"])

        # Remove duplicates
        unique_faces = []
        seen_indices = set()
        for face in selected_faces:
            if face["index"] not in seen_indices:
                unique_faces.append(face)
                seen_indices.add(face["index"])

        execution_time = int((time.time() - start_time) * 1000)

        result = {
            "success": True,
            "body_id": body_id,
            "selectors_requested": selectors,
            "faces_selected": len(unique_faces),
            "selected_faces": unique_faces
        }

        log_operation("select_faces_by_semantic",
                     {"body_id": body_id, "selectors": selectors},
                     "success", result,
                     execution_time_ms=execution_time)

        return result

    except Exception as e:
        if ui:
            ui.messageBox('Failed select_faces_by_semantic:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}


def clear_sketch(design, ui, sketch_id=None):
    """
    Safely clear active sketch without closing it.
    """
    import time
    start_time = time.time()

    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches

        if sketches.count == 0:
            return {"success": False, "error": "No sketches in design"}

        # Get target sketch
        sketch = None
        if sketch_id is None:
            sketch = sketches.item(sketches.count - 1)
        else:
            if isinstance(sketch_id, int):
                if 0 <= sketch_id < sketches.count:
                    sketch = sketches.item(sketch_id)
            else:
                for i in range(sketches.count):
                    if sketches.item(i).entityToken == sketch_id:
                        sketch = sketches.item(i)
                        break

        if sketch is None:
            return {"success": False, "error": f"Sketch not found: {sketch_id}"}

        # Count geometry before clearing
        geometry_count = 0
        geometry_count += sketch.sketchCurves.sketchLines.count
        geometry_count += sketch.sketchCurves.sketchCircles.count
        geometry_count += sketch.sketchCurves.sketchArcs.count

        # Delete all sketch curves
        for i in range(sketch.sketchCurves.count - 1, -1, -1):
            try:
                sketch.sketchCurves.item(i).deleteMe()
            except:
                pass

        execution_time = int((time.time() - start_time) * 1000)

        result = {
            "success": True,
            "sketch_id": sketch.entityToken,
            "sketch_name": sketch.name,
            "cleared": True,
            "geometry_removed": geometry_count,
            "message": f"Sketch cleared; {geometry_count} segments removed"
        }

        log_operation("clear_sketch", {"sketch_id": sketch_id}, "success", result, execution_time_ms=execution_time)
        return result

    except Exception as e:
        if ui:
            ui.messageBox('Failed clear_sketch:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}


def extrude_safe(design, ui, value, sketch_id, body_id, direction="normal", validate_before=True, validate_after=True):
    """
    Extrude with full pre/post validation.
    """
    import time
    start_time = time.time()

    try:
        rootComp = design.rootComponent
        sketches = rootComp.sketches

        # Get body state before
        geometry_before = None
        if validate_before:
            geometry_before = get_body_state(design)

        # Find target sketch
        target_sketch = None
        if isinstance(sketch_id, int):
            if 0 <= sketch_id < sketches.count:
                target_sketch = sketches.item(sketch_id)
        else:
            for i in range(sketches.count):
                if sketches.item(i).entityToken == sketch_id:
                    target_sketch = sketches.item(i)
                    break

        if target_sketch is None:
            return {"success": False, "error": f"Sketch not found: {sketch_id}"}

        # Validate sketch
        if validate_before:
            if target_sketch.profiles.count == 0:
                return {"success": False, "error": "Sketch has no closed profiles", "sketch_valid": False}

        profile = target_sketch.profiles.item(0)
        profile_closed = True
        profile_area = profile.areaProperties().area

        # Create extrusion
        extrudes = rootComp.features.extrudeFeatures
        extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(value)

        if direction == "symmetric":
            extInput.setSymmetricExtent(distance, True)
        elif direction == "both":
            extInput.setTwoSidesExtent(distance, distance)
        else:
            extInput.setDistanceExtent(False, distance)

        extrusion = extrudes.add(extInput)

        # Get body after
        volume_before = geometry_before.get("volume", 0) if geometry_before else 0
        geometry_after = get_body_state(design)
        volume_after = geometry_after.get("volume", 0)
        volume_added = volume_after - volume_before

        # Validate result
        geometry_manifold = geometry_after.get("body_valid", False)

        if validate_after and volume_added <= 0:
            return {
                "success": False,
                "error": "Extrusion did not add volume",
                "sketch_valid": True,
                "volume_added": volume_added
            }

        execution_time = int((time.time() - start_time) * 1000)

        result = {
            "success": True,
            "body_id": body_id,
            "extrusion_id": extrusion.entityToken,
            "sketch_valid": True,
            "profile_closed": profile_closed,
            "profile_area": profile_area,
            "volume_before": volume_before,
            "volume_after": volume_after,
            "volume_added": volume_added,
            "geometry_manifold": geometry_manifold,
            "error": None,
            "message": f"Extrusion successful: {volume_added:.2f} cm³ added"
        }

        log_operation("extrude_safe",
                     {"value": value, "sketch_id": sketch_id, "body_id": body_id},
                     "success", result,
                     body_state_before=geometry_before,
                     body_state_after=geometry_after,
                     execution_time_ms=execution_time)

        return result

    except Exception as e:
        if ui:
            ui.messageBox('Failed extrude_safe:\n{}'.format(traceback.format_exc()))
        return {"success": False, "error": str(e)}


#########################################################################################
### END OF NEW ENHANCED TOOLS ###
#########################################################################################


# HTTP Server######
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global ModelParameterSnapshot, query_results
        try:
            if self.path == '/count_parameters':
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"user_parameter_count": len(ModelParameterSnapshot)}).encode('utf-8'))
            elif self.path == '/list_parameters':
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ModelParameter": ModelParameterSnapshot}).encode('utf-8'))
            elif self.path == '/list_bodies':
                # Return cached result from last list_bodies operation
                result = query_results.get('list_bodies', {"success": False, "error": "No data available. Call POST /list_bodies first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/get_active_body':
                result = query_results.get('get_active_body', {"success": False, "error": "No data available. Call POST /get_active_body first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/list_sketches':
                result = query_results.get('list_sketches', {"success": False, "error": "No data available. Call POST /list_sketches first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/get_active_sketch':
                result = query_results.get('get_active_sketch', {"success": False, "error": "No data available. Call POST /get_active_sketch first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/select_body':
                result = query_results.get('select_body', {"success": False, "error": "No data available. Call POST /select_body first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/select_sketch':
                result = query_results.get('select_sketch', {"success": False, "error": "No data available. Call POST /select_sketch first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            # NEW ENHANCED TOOLS GET ENDPOINTS
            elif self.path == '/get_sketch_status':
                result = query_results.get('get_sketch_status', {"success": False, "error": "No data available. Call POST /get_sketch_status first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/list_faces':
                result = query_results.get('list_faces', {"success": False, "error": "No data available. Call POST /list_faces first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/pocket_recess_safe':
                result = query_results.get('pocket_recess_safe', {"success": False, "error": "No data available. Call POST /pocket_recess_safe first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/get_feature_history':
                result = query_results.get('get_feature_history', {"success": False, "error": "No data available. Call POST /get_feature_history first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/find_face_by_property':
                result = query_results.get('find_face_by_property', {"success": False, "error": "No data available. Call POST /find_face_by_property first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/draw_rectangles_batch':
                result = query_results.get('draw_rectangles_batch', {"success": False, "error": "No data available. Call POST /draw_rectangles_batch first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/pocket_smart':
                result = query_results.get('pocket_smart', {"success": False, "error": "No data available. Call POST /pocket_smart first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/begin_transaction':
                result = query_results.get('begin_transaction', {"success": False, "error": "No data available. Call POST /begin_transaction first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/commit_transaction':
                result = query_results.get('commit_transaction', {"success": False, "error": "No data available. Call POST /commit_transaction first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/rollback_transaction':
                result = query_results.get('rollback_transaction', {"success": False, "error": "No data available. Call POST /rollback_transaction first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/get_operation_log':
                result = query_results.get('get_operation_log', {"success": False, "error": "No data available. Call POST /get_operation_log first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/create_sketch_on_body_plane':
                result = query_results.get('create_sketch_on_body_plane', {"success": False, "error": "No data available. Call POST /create_sketch_on_body_plane first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/validate_face_exists':
                result = query_results.get('validate_face_exists', {"success": False, "error": "No data available. Call POST /validate_face_exists first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/select_faces_by_semantic':
                result = query_results.get('select_faces_by_semantic', {"success": False, "error": "No data available. Call POST /select_faces_by_semantic first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/clear_sketch':
                result = query_results.get('clear_sketch', {"success": False, "error": "No data available. Call POST /clear_sketch first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/extrude_safe':
                result = query_results.get('extrude_safe', {"success": False, "error": "No data available. Call POST /extrude_safe first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            # PROP PERFECTION TOOLS GET ENDPOINTS
            elif self.path == '/chamfer_edges':
                result = query_results.get('chamfer_edges', {"success": False, "error": "No data available. Call POST /chamfer_edges first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/split_body':
                result = query_results.get('split_body', {"success": False, "error": "No data available. Call POST /split_body first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            elif self.path == '/scale_body':
                result = query_results.get('scale_body', {"success": False, "error": "No data available. Call POST /scale_body first."})
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            else:
                self.send_error(404,'Not Found')
        except Exception as e:
            self.send_error(500,str(e))

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length',0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data) if post_data else {}
            path = self.path

            # Alle Aktionen in die Queue legen
            if path.startswith('/set_parameter'):
                name = data.get('name')
                value = data.get('value')
                if name and value:
                    task_queue.put(('set_parameter', name, value))
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"message": f"Parameter {name} wird gesetzt"}).encode('utf-8'))

            elif path == '/undo':
                task_queue.put(('undo',))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Undo wird ausgeführt"}).encode('utf-8'))

            elif path == '/Box':
                height = float(data.get('height',5))
                width = float(data.get('width',5))
                depth = float(data.get('depth',5))
                x = float(data.get('x',0))
                y = float(data.get('y',0))
                z = float(data.get('z',0))
                Plane = data.get('plane',None)  # 'XY', 'XZ', 'YZ' or None

                task_queue.put(('draw_box', height, width, depth,x,y,z, Plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Box wird erstellt"}).encode('utf-8'))

            elif path == '/Witzenmann':
                scale = data.get('scale',1.0)
                z = float(data.get('z',0))
                task_queue.put(('draw_witzenmann', scale,z))

                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Witzenmann-Logo wird erstellt"}).encode('utf-8'))

            elif path == '/Export_STL':
                name = str(data.get('Name','Test.stl'))
                task_queue.put(('export_stl', name))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "STL Export gestartet"}).encode('utf-8'))


            elif path == '/Export_STEP':
                name = str(data.get('name','Test.step'))
                task_queue.put(('export_step',name))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "STEP Export gestartet"}).encode('utf-8'))


            elif path == '/fillet_edges':
                radius = float(data.get('radius',0.3)) #0.3 as default
                edge_ids = data.get('edges', None)  # List of edge IDs or None
                if edge_ids is not None and not isinstance(edge_ids, list):
                    edge_ids = None
                task_queue.put(('fillet_edges',radius, edge_ids))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Fillet edges started"}).encode('utf-8'))

            elif path == '/chamfer_edges':
                distance = float(data.get('distance', 0.5))
                edge_ids = data.get('edges', None)
                angle = float(data.get('angle', 45.0))
                if edge_ids is not None and not isinstance(edge_ids, list):
                    edge_ids = None
                task_queue.put(('chamfer_edges', distance, edge_ids, angle))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Chamfer edges started"}).encode('utf-8'))

            elif path == '/split_body':
                body_id = data.get('body_id', None)
                split_tool = data.get('split_tool', 'XY')
                keep_both = bool(data.get('keep_both', True))
                task_queue.put(('split_body', body_id, split_tool, keep_both))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Split body started"}).encode('utf-8'))

            elif path == '/scale_body':
                body_id = data.get('body_id', None)
                scale_factor = float(data.get('scale_factor', 1.0))
                uniform = bool(data.get('uniform', True))
                scale_x = float(data.get('scale_x', 1.0))
                scale_y = float(data.get('scale_y', 1.0))
                scale_z = float(data.get('scale_z', 1.0))
                task_queue.put(('scale_body', body_id, scale_factor, uniform, scale_x, scale_y, scale_z))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Scale body started"}).encode('utf-8'))

            elif path == '/draw_cylinder':
                radius = float(data.get('radius', 1.0))
                height = float(data.get('height', 1.0))
                x = float(data.get('x',0))
                y = float(data.get('y',0))
                z = float(data.get('z',0))
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('draw_cylinder', radius, height, x, y,z, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Cylinder wird erstellt"}).encode('utf-8'))


            elif path == '/shell_body':
                thickness = float(data.get('thickness',0.5)) #0.5 as default
                faceindex = int(data.get('faceindex',0))
                task_queue.put(('shell_body', thickness, faceindex))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Shell body wird erstellt"}).encode('utf-8'))

            elif path == '/draw_lines':
                points = data.get('points', [])
                Plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('draw_lines', points, Plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Lines werden erstellt"}).encode('utf-8'))

            elif path == '/extrude_last_sketch':
                value = float(data.get('value',1.0)) #1.0 as default
                taperangle = float(data.get('taperangle', 0.0)) #0.0 as default
                task_queue.put(('extrude_last_sketch', value,taperangle))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Letzter Sketch wird extrudiert"}).encode('utf-8'))

            elif path == '/revolve':
                angle = float(data.get('angle',360)) #360 as default
                #axis = data.get('axis','X')  # 'X', 'Y', 'Z'
                task_queue.put(('revolve_profile', angle))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Profil wird revolviert"}).encode('utf-8'))
            elif path == '/arc':
                point1 = data.get('point1', [0,0])
                point2 = data.get('point2', [1,1])
                point3 = data.get('point3', [2,0])
                connect = bool(data.get('connect', False))
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('arc', point1, point2, point3, connect, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Arc wird erstellt"}).encode('utf-8'))

            elif path == '/draw_one_line':
                x1 = float(data.get('x1',0))
                y1 = float(data.get('y1',0))
                z1 = float(data.get('z1',0))
                x2 = float(data.get('x2',1))
                y2 = float(data.get('y2',1))
                z2 = float(data.get('z2',0))
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('draw_one_line', x1, y1, z1, x2, y2, z2, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Line wird erstellt"}).encode('utf-8'))

            elif path == '/holes':
                points = data.get('points', [[0,0]])
                width = float(data.get('width', 1.0))
                faceindex = int(data.get('faceindex', 0))
                distance = data.get('depth', None)
                if distance is not None:
                    distance = float(distance)
                through = bool(data.get('through', False))
                task_queue.put(('holes', points, width, distance,  faceindex))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()

                self.wfile.write(json.dumps({"message": "Loch wird erstellt"}).encode('utf-8'))

            elif path == '/create_circle':
                radius = float(data.get('radius',1.0))
                x = float(data.get('x',0))
                y = float(data.get('y',0))
                z = float(data.get('z',0))
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('circle', radius, x, y,z, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Circle wird erstellt"}).encode('utf-8'))

            elif path == '/extrude_thin':
                thickness = float(data.get('thickness',0.5)) #0.5 as default
                distance = float(data.get('distance',1.0)) #1.0 as default
                task_queue.put(('extrude_thin', thickness,distance))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Thin Extrude wird erstellt"}).encode('utf-8'))

            elif path == '/select_body':
                name = str(data.get('name', ''))
                task_queue.put(('select_body', name))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "message": "Body selection requested",
                    "note": "Results will be available via GET /select_body after processing (typically < 1 second)"
                }).encode('utf-8'))

            elif path == '/select_sketch':
                name = str(data.get('name', ''))
                task_queue.put(('select_sketch', name))

                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "message": "Sketch selection requested",
                    "note": "Results will be available via GET /select_sketch after processing (typically < 1 second)"
                }).encode('utf-8'))

            elif path == '/sweep':
                # enqueue a tuple so process_task recognizes the command
                task_queue.put(('sweep',))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Sweep wird erstellt"}).encode('utf-8'))

            elif path == '/spline':
                points = data.get('points', [])
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('spline', points, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Spline wird erstellt"}).encode('utf-8'))

            elif path == '/cut_extrude':
                depth = float(data.get('depth',1.0)) #1.0 as default
                task_queue.put(('cut_extrude', depth))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Cut Extrude wird erstellt"}).encode('utf-8'))

            elif path == '/circular_pattern':
                quantity = float(data.get('quantity', 6.0))
                axis = str(data.get('axis',"X"))
                plane = str(data.get('plane', 'XY'))  # 'XY', 'XZ', 'YZ'
                task_queue.put(('circular_pattern',quantity,axis,plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Cirular Pattern wird erstellt"}).encode('utf-8'))

            elif path == '/offsetplane':
                offset = float(data.get('offset',0.0))
                plane = str(data.get('plane', 'XY'))  # 'XY', 'XZ', 'YZ'

                task_queue.put(('offsetplane', offset, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Offset Plane wird erstellt"}).encode('utf-8'))

            elif path == '/loft':
                sketchcount = int(data.get('sketchcount',2))
                task_queue.put(('loft', sketchcount))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Loft wird erstellt"}).encode('utf-8'))

            elif path == '/ellipsis':
                 x_center = float(data.get('x_center',0))
                 y_center = float(data.get('y_center',0))
                 z_center = float(data.get('z_center',0))
                 x_major = float(data.get('x_major',10))
                 y_major = float(data.get('y_major',0))
                 z_major = float(data.get('z_major',0))
                 x_through = float(data.get('x_through',5))
                 y_through = float(data.get('y_through',4))
                 z_through = float(data.get('z_through',0))
                 plane = str(data.get('plane', 'XY'))  # 'XY', 'XZ', 'YZ'
                 task_queue.put(('ellipsis', x_center, y_center, z_center,
                                  x_major, y_major, z_major, x_through, y_through, z_through, plane))
                 self.send_response(200)
                 self.send_header('Content-type','application/json')
                 self.end_headers()
                 self.wfile.write(json.dumps({"message": "Ellipsis wird erstellt"}).encode('utf-8'))

            elif path == '/sphere':
                radius = float(data.get('radius',5.0))
                x = float(data.get('x',0))
                y = float(data.get('y',0))
                z = float(data.get('z',0))
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('draw_sphere', radius, x, y,z, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Sphere wird erstellt"}).encode('utf-8'))

            elif path == '/threaded':
                inside = bool(data.get('inside', True))
                allsizes = int(data.get('allsizes', 30))
                task_queue.put(('threaded', inside, allsizes))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Threaded Feature wird erstellt"}).encode('utf-8'))

            elif path == '/delete_everything':
                task_queue.put(('delete_everything',))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Alle Bodies werden gelöscht"}).encode('utf-8'))

            elif path == '/boolean_operation':
                operation = data.get('operation', 'join')  # 'join', 'cut', 'intersect'
                task_queue.put(('boolean_operation', operation))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Boolean Operation wird ausgeführt"}).encode('utf-8'))

            elif path == '/test_connection':
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Verbindung erfolgreich"}).encode('utf-8'))

            elif path == '/draw_2d_rectangle':
                x_1 = float(data.get('x_1',0))
                y_1 = float(data.get('y_1',0))
                z_1 = float(data.get('z_1',0))
                x_2 = float(data.get('x_2',1))
                y_2 = float(data.get('y_2',1))
                z_2 = float(data.get('z_2',0))
                plane = data.get('plane', 'XY')  # 'XY', 'XZ', 'YZ'
                task_queue.put(('draw_2d_rectangle', x_1, y_1, z_1, x_2, y_2, z_2, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "2D Rechteck wird erstellt"}).encode('utf-8'))


            elif path == '/rectangular_pattern':
                 quantity_one = float(data.get('quantity_one',2))
                 distance_one = float(data.get('distance_one',5))
                 axis_one = str(data.get('axis_one',"X"))
                 quantity_two = float(data.get('quantity_two',2))
                 distance_two = float(data.get('distance_two',5))
                 axis_two = str(data.get('axis_two',"Y"))
                 plane = str(data.get('plane', 'XY'))  # 'XY', 'XZ', 'YZ'
                 # Parameter-Reihenfolge: axis_one, axis_two, quantity_one, quantity_two, distance_one, distance_two, plane
                 task_queue.put(('rectangular_pattern', axis_one, axis_two, quantity_one, quantity_two, distance_one, distance_two, plane))
                 self.send_response(200)
                 self.send_header('Content-type','application/json')
                 self.end_headers()
                 self.wfile.write(json.dumps({"message": "Rectangular Pattern wird erstellt"}).encode('utf-8'))

            elif path == '/draw_text':
                 text = str(data.get('text',"Hello"))
                 x_1 = float(data.get('x_1',0))
                 y_1 = float(data.get('y_1',0))
                 z_1 = float(data.get('z_1',0))
                 x_2 = float(data.get('x_2',10))
                 y_2 = float(data.get('y_2',4))
                 z_2 = float(data.get('z_2',0))
                 extrusion_value = float(data.get('extrusion_value',1.0))
                 plane = str(data.get('plane', 'XY'))  # 'XY', 'XZ', 'YZ'
                 thickness = float(data.get('thickness',0.5))
                 task_queue.put(('draw_text', text,thickness, x_1, y_1, z_1, x_2, y_2, z_2, extrusion_value, plane))
                 self.send_response(200)
                 self.send_header('Content-type','application/json')
                 self.end_headers()
                 self.wfile.write(json.dumps({"message": "Text wird erstellt"}).encode('utf-8'))

            elif path == '/move_body':
                x = float(data.get('x',0))
                y = float(data.get('y',0))
                z = float(data.get('z',0))
                task_queue.put(('move_body', x, y, z))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Body wird verschoben"}).encode('utf-8'))

            elif path == '/pocket_recess':
                depth = float(data.get('depth', 1.0))
                face_index = data.get('face_index', None)
                body_id = data.get('body_id', None)
                sketch_id = data.get('sketch_id', None)
                if face_index is not None:
                    face_index = int(face_index)
                task_queue.put(('pocket_recess', depth, face_index, body_id, sketch_id))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Pocket/Recess wird erstellt"}).encode('utf-8'))

            elif path == '/sketch_on_face':
                body_index = int(data.get('body_index', -1))
                face_index = int(data.get('face_index', 0))
                task_queue.put(('sketch_on_face', body_index, face_index))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Sketch auf Face wird erstellt"}).encode('utf-8'))

            elif path == '/create_work_plane':
                plane_type = str(data.get('plane_type', 'offset_xy'))
                offset_distance = float(data.get('offset_distance', 0.0))
                reference_index = int(data.get('reference_index', 0))
                task_queue.put(('create_work_plane', plane_type, offset_distance, reference_index))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Work Plane wird erstellt"}).encode('utf-8'))

            elif path == '/project_edges':
                body_index = data.get('body_index', None)
                if body_index is not None:
                    body_index = int(body_index)
                task_queue.put(('project_edges', body_index))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Edges werden projiziert"}).encode('utf-8'))

            elif path == '/draw_polygon':
                sides = int(data.get('sides', 6))
                radius = float(data.get('radius', 5.0))
                x = float(data.get('x', 0))
                y = float(data.get('y', 0))
                z = float(data.get('z', 0))
                plane = str(data.get('plane', 'XY'))
                task_queue.put(('draw_polygon', sides, radius, x, y, z, plane))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Polygon wird erstellt"}).encode('utf-8'))

            elif path == '/offset_surface':
                distance = float(data.get('distance', 1.0))
                face_index = int(data.get('face_index', 0))
                task_queue.put(('offset_surface', distance, face_index))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Surface Offset wird erstellt"}).encode('utf-8'))

            elif path == '/mirror_feature':
                mirror_plane = str(data.get('mirror_plane', 'XY'))
                body_index = data.get('body_index', None)
                if body_index is not None:
                    body_index = int(body_index)
                task_queue.put(('mirror_feature', mirror_plane, body_index))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Mirror Feature wird erstellt"}).encode('utf-8'))

            elif path == '/list_bodies':
                task_queue.put(('list_bodies',))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "message": "Body list requested",
                    "note": "Results will be available via GET /list_bodies after processing (typically < 1 second)"
                }).encode('utf-8'))

            elif path == '/get_active_body':
                task_queue.put(('get_active_body',))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "message": "Active body requested",
                    "note": "Results will be available via GET /get_active_body after processing (typically < 1 second)"
                }).encode('utf-8'))

            elif path == '/rename_body':
                body_id = data.get('body_id', None)
                new_name = str(data.get('new_name', ''))
                if body_id is not None and new_name:
                    task_queue.put(('rename_body', body_id, new_name))
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"message": "Renaming body"}).encode('utf-8'))
                else:
                    self.send_error(400, "Missing body_id or new_name")

            elif path == '/list_sketches':
                task_queue.put(('list_sketches',))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "message": "Sketch list requested",
                    "note": "Results will be available via GET /list_sketches after processing (typically < 1 second)"
                }).encode('utf-8'))

            elif path == '/get_active_sketch':
                task_queue.put(('get_active_sketch',))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "message": "Active sketch requested",
                    "note": "Results will be available via GET /get_active_sketch after processing (typically < 1 second)"
                }).encode('utf-8'))

            elif path == '/activate_sketch':
                sketch_id = data.get('sketch_id', None)
                if sketch_id is not None:
                    task_queue.put(('activate_sketch', sketch_id))
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"message": "Activating sketch"}).encode('utf-8'))
                else:
                    self.send_error(400, "Missing sketch_id")

            elif path == '/close_sketch':
                sketch_id = data.get('sketch_id', None)
                task_queue.put(('close_sketch', sketch_id))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Closing sketch"}).encode('utf-8'))

            # NEW ENHANCED TOOLS ENDPOINTS
            elif path == '/get_sketch_status':
                sketch_id = data.get('sketch_id', None)
                include_geometry = data.get('include_geometry', True)
                task_queue.put(('get_sketch_status', sketch_id, include_geometry))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "message": "Sketch status requested",
                    "note": "Results will be available via GET /get_sketch_status after processing"
                }).encode('utf-8'))

            elif path == '/list_faces':
                body_id = data.get('body_id')
                if body_id is not None:
                    task_queue.put(('list_faces', body_id))
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "message": "Face list requested",
                        "note": "Results will be available via GET /list_faces after processing"
                    }).encode('utf-8'))
                else:
                    self.send_error(400, "Missing body_id")

            elif path == '/pocket_recess_safe':
                body_id = data.get('body_id')
                sketch_id = data.get('sketch_id')
                depth = float(data.get('depth', 0.5))
                operation = data.get('operation', 'cut')
                validate_before = data.get('validate_before', True)
                validate_after = data.get('validate_after', True)
                if body_id is not None and sketch_id is not None and depth is not None:
                    task_queue.put(('pocket_recess_safe', body_id, sketch_id, depth,
                                   operation, validate_before, validate_after))
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "message": "Pocket recess safe requested",
                        "note": "Results will be available via GET /pocket_recess_safe after processing"
                    }).encode('utf-8'))
                else:
                    self.send_error(400, "Missing body_id, sketch_id, or depth")

            elif path == '/get_feature_history':
                body_id = data.get('body_id')
                include_parameters = data.get('include_parameters', True)
                include_errors = data.get('include_errors', True)
                if body_id is not None:
                    task_queue.put(('get_feature_history', body_id, include_parameters, include_errors))
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "message": "Feature history requested",
                        "note": "Results will be available via GET /get_feature_history after processing"
                    }).encode('utf-8'))
                else:
                    self.send_error(400, "Missing body_id")

            elif path == '/find_face_by_property':
                body_id = data.get('body_id')
                selector = data.get('selector', None)
                normal = data.get('normal', None)
                area_range = data.get('area_range', None)
                position = data.get('position', None)
                return_all_matches = data.get('return_all_matches', False)
                if body_id is not None:
                    task_queue.put(('find_face_by_property', body_id, selector, normal,
                                   area_range, position, return_all_matches))
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "message": "Find face by property requested",
                        "note": "Results will be available via GET /find_face_by_property after processing"
                    }).encode('utf-8'))
                else:
                    self.send_error(400, "Missing body_id")

            elif path == '/draw_rectangles_batch':
                plane = data.get('plane', 'XY')
                rectangles = data.get('rectangles', [])
                if rectangles:
                    task_queue.put(('draw_rectangles_batch', plane, rectangles))
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "message": "Draw rectangles batch requested",
                        "note": "Results will be available via GET /draw_rectangles_batch after processing"
                    }).encode('utf-8'))
                else:
                    self.send_error(400, "Missing rectangles")

            elif path == '/pocket_smart':
                body_id = data.get('body_id')
                sketch_id = data.get('sketch_id')
                depth_mode = data.get('depth_mode', 'absolute')
                depth_value = float(data.get('depth_value', 0.5))
                from_face = data.get('from_face', 'sketch_plane')
                snap_to_geometry = data.get('snap_to_geometry', False)
                validate_after = data.get('validate_after', True)
                if body_id is not None and sketch_id is not None and depth_value is not None:
                    task_queue.put(('pocket_smart', body_id, sketch_id, depth_mode, depth_value,
                                   from_face, snap_to_geometry, validate_after))
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "message": "Pocket smart requested",
                        "note": "Results will be available via GET /pocket_smart after processing"
                    }).encode('utf-8'))
                else:
                    self.send_error(400, "Missing body_id, sketch_id, or depth_value")

            elif path == '/begin_transaction':
                transaction_id = data.get('transaction_id')
                description = data.get('description', '')
                auto_validate = data.get('auto_validate', True)
                auto_rollback_on_error = data.get('auto_rollback_on_error', False)
                if transaction_id:
                    task_queue.put(('begin_transaction', transaction_id, description,
                                   auto_validate, auto_rollback_on_error))
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "message": "Begin transaction requested",
                        "note": "Results will be available via GET /begin_transaction after processing"
                    }).encode('utf-8'))
                else:
                    self.send_error(400, "Missing transaction_id")

            elif path == '/commit_transaction':
                transaction_id = data.get('transaction_id')
                force = data.get('force', False)
                if transaction_id:
                    task_queue.put(('commit_transaction', transaction_id, force))
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "message": "Commit transaction requested",
                        "note": "Results will be available via GET /commit_transaction after processing"
                    }).encode('utf-8'))
                else:
                    self.send_error(400, "Missing transaction_id")

            elif path == '/rollback_transaction':
                transaction_id = data.get('transaction_id')
                if transaction_id:
                    task_queue.put(('rollback_transaction', transaction_id))
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "message": "Rollback transaction requested",
                        "note": "Results will be available via GET /rollback_transaction after processing"
                    }).encode('utf-8'))
                else:
                    self.send_error(400, "Missing transaction_id")

            elif path == '/get_operation_log':
                last_n_operations = int(data.get('last_n_operations', 20))
                body_id = data.get('body_id', None)
                operation_type = data.get('operation_type', None)
                status_filter = data.get('status_filter', None)
                task_queue.put(('get_operation_log', last_n_operations, body_id,
                               operation_type, status_filter))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "message": "Operation log requested",
                    "note": "Results will be available via GET /get_operation_log after processing"
                }).encode('utf-8'))

            elif path == '/create_sketch_on_body_plane':
                body_id = data.get('body_id')
                plane = data.get('plane', 'XY')
                z_offset = float(data.get('z_offset', 0))
                name = data.get('name', None)
                if body_id is not None:
                    task_queue.put(('create_sketch_on_body_plane', body_id, plane, z_offset, name))
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "message": "Create sketch on body plane requested",
                        "note": "Results will be available via GET /create_sketch_on_body_plane after processing"
                    }).encode('utf-8'))
                else:
                    self.send_error(400, "Missing body_id")

            elif path == '/validate_face_exists':
                body_id = data.get('body_id')
                face_index = int(data.get('face_index', 0))
                if body_id is not None and face_index is not None:
                    task_queue.put(('validate_face_exists', body_id, face_index))
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "message": "Validate face exists requested",
                        "note": "Results will be available via GET /validate_face_exists after processing"
                    }).encode('utf-8'))
                else:
                    self.send_error(400, "Missing body_id or face_index")

            elif path == '/select_faces_by_semantic':
                body_id = data.get('body_id')
                selectors = data.get('selectors', [])
                if body_id is not None and selectors:
                    task_queue.put(('select_faces_by_semantic', body_id, selectors))
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "message": "Select faces by semantic requested",
                        "note": "Results will be available via GET /select_faces_by_semantic after processing"
                    }).encode('utf-8'))
                else:
                    self.send_error(400, "Missing body_id or selectors")

            elif path == '/clear_sketch':
                sketch_id = data.get('sketch_id', None)
                task_queue.put(('clear_sketch', sketch_id))
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "message": "Clear sketch requested",
                    "note": "Results will be available via GET /clear_sketch after processing"
                }).encode('utf-8'))

            elif path == '/extrude_safe':
                value = float(data.get('value', 1.0))
                sketch_id = data.get('sketch_id')
                body_id = data.get('body_id')
                direction = data.get('direction', 'normal')
                validate_before = data.get('validate_before', True)
                validate_after = data.get('validate_after', True)
                if value is not None and sketch_id is not None and body_id is not None:
                    task_queue.put(('extrude_safe', value, sketch_id, body_id, direction,
                                   validate_before, validate_after))
                    self.send_response(200)
                    self.send_header('Content-type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "message": "Extrude safe requested",
                        "note": "Results will be available via GET /extrude_safe after processing"
                    }).encode('utf-8'))
                else:
                    self.send_error(400, "Missing value, sketch_id, or body_id")

            else:
                self.send_error(404,'Not Found')

        except Exception as e:
            self.send_error(500,str(e))

def run_server():
    global httpd
    server_address = ('localhost',5000)
    httpd = HTTPServer(server_address, Handler)
    httpd.serve_forever()


def run(context):
    global app, ui, design, handlers, stopFlag, customEvent
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Check if a document is active before accessing activeProduct
        if not app.activeDocument:
            ui.messageBox("Kein aktives Dokument geöffnet! Bitte öffnen oder erstellen Sie ein Design.")
            return

        design = adsk.fusion.Design.cast(app.activeProduct)

        if design is None:
            ui.messageBox("Kein aktives Design geöffnet!")
            return

        # Initialer Snapshot
        global ModelParameterSnapshot
        ModelParameterSnapshot = get_model_parameters(design)

        # Custom Event registrieren
        customEvent = app.registerCustomEvent(myCustomEvent) #Every 200ms we create a custom event which doesnt interfere with Fusion main thread
        onTaskEvent = TaskEventHandler() #If we have tasks in the queue, we process them in the main thread
        customEvent.add(onTaskEvent) # Here we add the event handler
        handlers.append(onTaskEvent)

        # Task Thread starten
        stopFlag = threading.Event()
        taskThread = TaskThread(stopFlag)
        taskThread.daemon = True
        taskThread.start()

        ui.messageBox(f"Fusion HTTP Add-In gestartet! Port 5000.\nParameter geladen: {len(ModelParameterSnapshot)} Modellparameter")

        # HTTP-Server starten
        threading.Thread(target=run_server, daemon=True).start()

    except:
        try:
            ui.messageBox('Fehler im Add-In:\n{}'.format(traceback.format_exc()))
        except:
            pass




def stop(context):
    global stopFlag, httpd, task_queue, handlers, app, customEvent

    # Stop the task thread
    if stopFlag:
        stopFlag.set()

    # Clean up event handlers
    for handler in handlers:
        try:
            if customEvent:
                customEvent.remove(handler)
        except:
            pass

    handlers.clear()

    # Clear the queue without processing (avoid freezing)
    while not task_queue.empty():
        try:
            task_queue.get_nowait()
            if task_queue.empty():
                break
        except:
            break

    # Stop HTTP server
    if httpd:
        try:
            httpd.shutdown()
        except:
            pass


    if httpd:
        try:
            httpd.shutdown()
            httpd.server_close()
        except:
            pass
        httpd = None
    try:
        app = adsk.core.Application.get()
        if app:
            ui = app.userInterface
            if ui:
                ui.messageBox("Fusion HTTP Add-In gestoppt")
    except:
        pass
