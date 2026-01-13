# Prop Replica & Custom PC Case Creation Guide

This guide demonstrates how to use the Fusion MCP Integration to create detailed prop replicas that can be converted into custom PC cases.

## 🎯 Overview

The Fusion MCP server provides a comprehensive set of tools for creating complex 3D models through conversational AI. This guide focuses on creating prop replicas with the specific consideration that they will house PC components.

## 📋 Prerequisites

- Fusion 360 installed and running
- MCP Add-in installed and activated
- MCP Server connected to Claude Desktop or VS Code Copilot
- Reference images or measurements of the prop to replicate

## 🔧 Available Tools for Prop Replica Creation

### Basic Shapes
- `draw_box` - Create rectangular boxes with precise dimensions
- `draw_cylinder` - Create cylindrical forms
- `draw_sphere` - Create spherical shapes
- `draw_polygon` - Create regular polygons (hexagons, octagons, etc.)

### Sketching Tools
- `draw2Dcircle` - Create 2D circles for profiles
- `draw_lines` - Create polylines (connected line segments)
- `draw_one_line` - Create a single line
- `arc` - Create circular arcs
- `spline` - Create smooth curves through points
- `ellipsie` - Create elliptical shapes
- `draw_text` - Add text that can be extruded

### Feature Creation
- `extrude` - Extrude sketches into 3D bodies
- `extrude_thin` - Create thin-walled extrusions (pipes, shells)
- `revolve` - Create bodies by revolving profiles around an axis
- `sweep` - Sweep a profile along a path
- `loft` - Create smooth transitions between multiple profiles

### Modification Tools
- `cut_extrude` - Remove material by extruding a sketch
- `pocket_recess` - Create depressions in surfaces
- `fillet_edges` - Round sharp edges
- `shell_body` - Hollow out bodies with uniform wall thickness

### Advanced Sketching
- `sketch_on_face` - Create sketches directly on body faces
- `create_work_plane` - Create offset construction planes
- `project_edges` - Project body edges onto sketch planes

### Patterns & Symmetry
- `circular_pattern` - Create circular arrays of features
- `rectangular_pattern` - Create rectangular arrays
- `mirror_feature` - Mirror features across planes

### Boolean Operations
- `boolean_operation` - Combine, cut, or intersect bodies

### Hardware Features
- `draw_holes` - Create counterbore holes for mounting
- `create_thread` - Add threading to holes

### Export
- `export_step` - Export as STEP file (for CAD)
- `export_stl` - Export as STL file (for 3D printing/CNC)

## 📐 Key Measurements for PC Cases

**IMPORTANT: In Fusion 360, 1 unit = 1 cm = 10 mm**

### Motherboard Standards
- **ATX**: 30.5 × 24.4 cm (305 × 244 mm)
  - 9-12 mounting holes in standard pattern
- **MicroATX**: 24.4 × 24.4 cm (244 × 244 mm)
  - 6-7 mounting holes
- **Mini-ITX**: 17 × 17 cm (170 × 170 mm)
  - 4 mounting holes

### Component Clearances
- Wall thickness: 0.3-0.5 cm (3-5 mm)
- Motherboard standoff height: 0.6-0.8 cm (6-8 mm)
- Motherboard clearance from side: 2-3 cm
- PSU clearance: minimum 1 cm on all sides
- GPU clearance: 30-40 cm length, 15-16 cm height
- CPU cooler clearance: 15-17 cm height

### Mounting Hardware
- Motherboard standoff holes: 0.3 cm diameter (3mm for M3 screws)
- PSU mounting holes: 0.4 cm diameter (4mm)
- Fan mounting holes: 0.45 cm diameter (4.5mm)
- Ventilation holes: 0.5-1.5 cm (hexagons or circles)

### Standard PSU Dimensions
- ATX PSU: 15 × 8.6 × 14 cm (150 × 86 × 140 mm)
- SFX PSU: 12.5 × 6.35 × 10 cm (125 × 63.5 × 100 mm)

## 🛠️ Workflow: Creating a Prop Replica PC Case

### Phase 1: Planning & Reference

1. **Gather References**
   - Collect images from multiple angles
   - Note key dimensions and proportions
   - Identify which parts will be structural vs decorative

2. **Plan PC Component Layout**
   - Determine motherboard size (ATX/mATX/ITX)
   - Plan PSU location (top, bottom, side)
   - Identify space for GPU, drives, cooling
   - Plan cable routing paths

### Phase 2: Main Structure

```
Example workflow in Claude/Copilot:

"Create the main body of a prop replica case:
- Base dimensions: 40cm wide × 45cm deep × 35cm tall
- Wall thickness: 4mm
- Hollow interior for components"

The AI will execute:
1. delete_all()
2. draw_box(height="35", width="40", depth="45", x=0, y=0, z=0, plane="XY")
3. shell_body(thickness=0.4, faceindex=4)  # Remove top face
```

### Phase 3: Ventilation System

```
"Add hexagonal ventilation pattern to the front panel:
- 8mm hexagons
- 5 columns × 8 rows
- 3cm spacing"

The AI will execute:
1. sketch_on_face(body_index=-1, face_index=0)  # Front face
2. draw_polygon(sides=6, radius=0.8, x=0, y=0, z=0, plane="XY")
3. rectangular_pattern(plane="XY", quantity_one=5, quantity_two=8, 
                      distance_one=30, distance_two=30, axis_one="X", axis_two="Y")
4. pocket_recess(depth=0.5)
```

### Phase 4: Mounting Points

```
"Add ATX motherboard mounting holes on the right side panel"

The AI will calculate and execute:
1. sketch_on_face(body_index=-1, face_index=2)
2. draw_holes(points=[[2.44, 5.08], [2.44, 16.51], [2.44, 22.86], 
                     [16.51, 2.54], [16.51, 22.86], [28.45, 2.54], 
                     [28.45, 16.51], [28.45, 22.86]], 
             width=0.3, depth=0.5, faceindex=2)
```

```
"Add PSU mounting holes on the bottom panel"

The AI will execute:
1. sketch_on_face(body_index=-1, face_index=5)
2. draw_holes(points=[[7.5, 3.5], [7.5, 10.5], [22.5, 3.5], [22.5, 10.5]], 
             width=0.4, depth=0.5, faceindex=5)
```

### Phase 5: Decorative Details

```
"Add recessed panels with rounded edges"

The AI will execute:
1. sketch_on_face(body_index=-1, face_index=0)
2. draw2Dcircle(radius=8, x=5, y=5, z=0, plane="XY")
3. pocket_recess(depth=0.3)
4. fillet_edges(radius=0.5)
```

### Phase 6: Access Ports & Cutouts

```
"Create I/O cutout for motherboard rear panel - 15.8cm × 4.4cm"

The AI will execute:
1. sketch_on_face(body_index=-1, face_index=1)  # Rear face
2. draw_box(height="4.4", width="15.8", depth="0.5", x=0, y=15, z=0)
3. cut_extrude(depth=5)  # Cut through
```

### Phase 7: Symmetry & Finishing

```
"Mirror the side panel details to the opposite side"

The AI will execute:
1. mirror_feature(mirror_plane="YZ", body_index=-1)
```

```
"Round all sharp external edges with 3mm radius"

The AI will execute:
1. fillet_edges(radius=0.3)
```

### Phase 8: Export

```
"Export the model for 3D printing and CAD"

The AI will execute:
1. export_step(name="prop_replica_case_v1")
2. export_stl(name="prop_replica_case_v1")
```

## 💡 Tips & Best Practices

### Design Tips

1. **Start Simple**: Build the basic structure first, add details progressively
2. **Layer Approach**: Use multiple extrudes and loft operations for complex shapes
3. **Reference Planes**: Use `create_work_plane` for angled features
4. **Symmetry First**: Design one side perfectly, then mirror
5. **Test Fit**: Verify component clearances before finalizing

### Technical Considerations

1. **Wall Thickness**: 
   - Minimum 3mm for structural integrity
   - 4-5mm for mounting points
   - Consider material (PLA, PETG, etc.)

2. **Ventilation**:
   - At least 30% open area for airflow
   - Align intake and exhaust
   - Consider dust filters

3. **Assembly**:
   - Design for printability (no support-heavy overhangs)
   - Plan assembly sequence
   - Include alignment features

4. **Cable Management**:
   - Add cable routing channels
   - Include tie-down points
   - Plan for wire thickness

### Common Issues & Solutions

**Issue**: Parts don't align after printing
- **Solution**: Add alignment pins using `draw_cylinder` (2-3mm diameter)

**Issue**: Insufficient cooling
- **Solution**: Use `circular_pattern` to add more vent holes

**Issue**: Motherboard doesn't fit
- **Solution**: Always verify against standard dimensions, add 2-3mm clearance

**Issue**: Parts too large to print
- **Solution**: Design in sections, use `draw_lines` to mark cutting planes

## 🎨 Example Projects

### Example 1: Sci-Fi Prop Replica Case

```
Prompt: "Create a futuristic sci-fi case with hexagonal panels:
- Base: 35cm × 35cm × 40cm tall
- Hexagonal ventilation on all sides
- Central circular viewing window
- Support for Mini-ITX motherboard
- Integrated LED strip channels"
```

### Example 2: Retro Computer Replica

```
Prompt: "Create a replica of a 1980s computer case:
- Beige rectangular case: 45cm × 40cm × 15cm
- Front panel with 5.25" drive bay cutouts
- Ribbed side panels for style
- Support for MicroATX motherboard
- Vintage-style vent pattern"
```

### Example 3: Steampunk PC Case

```
Prompt: "Create a steampunk-inspired case:
- Brass-style riveted panels
- Circular porthole windows
- Gear-shaped ventilation
- Victorian-era aesthetic
- Support for ATX motherboard"
```

## 📚 Prompt Templates

### Quick Start Template
```
"Create a PC case with these specs:
- Motherboard: [ATX/mATX/ITX]
- Dimensions: [W]cm × [D]cm × [H]cm
- Style: [modern/retro/sci-fi/etc]
- Features: [windows, RGB channels, etc]
- Ventilation: [front/top/side]"
```

### Detailed Template
```
"I need to create a 3D model of a prop replica that will become a PC case.

Reference: [description or image]

Requirements:
- Main body dimensions: [W × D × H]
- Motherboard form factor: [size]
- PSU location: [top/bottom/side]
- Ventilation style: [hexagons/circles/slits]
- Special features: [windows, panels, etc]
- Material thickness: [3-5mm]

Please create this step by step, starting with the main structure."
```

## 🔍 Tool Reference Quick Guide

| Task | Tool to Use |
|------|-------------|
| Create main body | `draw_box`, `draw_cylinder` |
| Hollow out interior | `shell_body` |
| Add vent holes | `draw_polygon` + `pocket_recess` |
| Repeat vents | `rectangular_pattern`, `circular_pattern` |
| Motherboard holes | `draw_holes` |
| I/O cutouts | `draw2Dcircle` + `cut_extrude` |
| Round edges | `fillet_edges` |
| Symmetric features | `mirror_feature` |
| Complex shapes | `loft`, `sweep`, `revolve` |
| Panel details | `sketch_on_face` + `pocket_recess` |
| Export files | `export_step`, `export_stl` |

## 🚀 Getting Started

1. **Activate the Fusion Add-in** in Fusion 360
2. **Start the MCP Server** (`python MCP_Server.py`)
3. **Open Claude Desktop** or **VS Code with Copilot**
4. **Use the prompt**: `/mcp.FusionMCP` (VS Code) or select from MCP list (Claude)
5. **Start with**: "I need help creating a prop replica PC case"

The AI assistant will guide you through the entire process, using all available tools to bring your design to life!

## 📖 Additional Resources

- [Fusion 360 Documentation](https://help.autodesk.com/view/fusion360/)
- [PC Case Building Standards](https://www.reddit.com/r/buildapc/)
- [3D Printing for PC Cases](https://www.reddit.com/r/3Dprinting/)

## 🤝 Contributing

Found a useful workflow? Have a cool prop replica example? Contributions are welcome!

---

**Remember**: This is a proof-of-concept tool. Always verify dimensions and test-fit components before final fabrication. The AI assistant is here to help, but you should review all generated geometry for accuracy.
