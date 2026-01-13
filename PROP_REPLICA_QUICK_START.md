# Prop Replica PC Case - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

This guide will help you quickly start creating a prop replica that functions as a custom PC case.

## Step 1: Setup (One Time)

1. **Install and activate** the Fusion 360 MCP Add-in
2. **Start the MCP server**:
   ```bash
   cd Server
   python MCP_Server.py
   ```
3. **Open Claude Desktop** or **VS Code with Copilot**

## Step 2: Start Your Project

In Claude or Copilot, type one of these:

### Option A: Use the Interactive Prompt
```
/mcp.FusionMCP
```
Then select: **custom_prop_case_from_reference**

### Option B: Direct Request
```
I want to create a prop replica PC case. Can you help me convert [describe your prop] into a functional PC case that will house [ATX/mATX/ITX] components?
```

### Option C: Use the Comprehensive Workflow
```
/mcp.FusionMCP
```
Then select: **prop_replica_pc_case**

## Step 3: Provide Reference Information

The AI will ask you for:
- **Rough dimensions** of your prop (e.g., "40cm wide, 45cm deep, 35cm tall")
- **Motherboard size** you want to support (ATX, MicroATX, or Mini-ITX)
- **Key features** from the prop you want to preserve
- **Reference images** description (if available)

## Step 4: Follow the Workflow

The AI will guide you through:

1. **Creating the base structure** - Main body shape
2. **Hollowing it out** - Interior space for components
3. **Adding mounting points** - Motherboard, PSU, drives
4. **Creating ventilation** - Cooling holes/patterns
5. **Adding details** - Decorative elements from the prop
6. **Finishing touches** - Rounded edges, refinements
7. **Exporting files** - STEP and STL for fabrication

## Key Commands You'll See

The AI will use these tools automatically:

| What It Does | Tool Used |
|--------------|-----------|
| Clear workspace | `delete_all()` |
| Create main body | `draw_box()` or `draw_cylinder()` |
| Hollow interior | `shell_body(thickness=0.4)` |
| Add vent holes | `draw_polygon(sides=6)` + `pocket_recess()` |
| Repeat pattern | `rectangular_pattern()` or `circular_pattern()` |
| Mount holes | `draw_holes()` |
| Round edges | `fillet_edges()` |
| Export files | `export_step()`, `export_stl()` |

## Important Units Reminder

**In Fusion 360: 1 unit = 1 cm = 10 mm**

Examples:
- 3mm wall thickness = 0.3
- 305mm ATX board = 30.5
- 5mm vent hole = 0.5

## Example Session

```
You: "I want to make a sci-fi themed PC case, roughly 40cm x 40cm x 35cm for a Mini-ITX build"

AI: "Great! I'll help you create that. Let me start by:
1. Creating the main 40x40x35cm body
2. Hollowing it out with 4mm walls
3. Adding Mini-ITX mounting holes
4. Creating a hexagonal vent pattern for sci-fi aesthetic
5. Adding details

Let's begin..."

[AI executes the workflow automatically]

AI: "I've created the base structure. Would you like me to:
- Add more ventilation on specific panels?
- Create recessed decorative panels?
- Add lighting channels?
- Modify any dimensions?"

You: "Add hexagonal vents to the front panel"

AI: "Adding hexagonal ventilation array to front panel..."
[AI creates the pattern]

AI: "Done! The front panel now has ventilation. Ready to export?"

You: "Yes, export it"

AI: "Exporting as STEP and STL files..."
```

## Quick Tips

✅ **DO:**
- Start with overall dimensions
- Think about component clearances (add 2-3cm)
- Ask for ventilation (cooling is critical!)
- Request rounded edges (looks better, safer to handle)
- Export early and often

❌ **DON'T:**
- Forget about interior clearances
- Skip ventilation planning
- Make walls too thin (minimum 3mm)
- Forget cable routing space

## Component Clearances to Remember

- **Motherboard heights**: ATX = 30.5cm, mATX = 24.4cm, ITX = 17cm
- **GPU length**: Plan for 30-35cm if gaming
- **CPU cooler**: 15-17cm height typical
- **PSU space**: 15cm x 8.6cm x 14cm + 1cm clearance
- **Cables**: Add 3-5cm behind motherboard for routing

## Getting Help

If stuck, ask:
- "Can you explain what this step does?"
- "Can you show me the motherboard mounting positions?"
- "How do I add more ventilation?"
- "Can you mirror this feature to the other side?"

## What's Next?

After the AI creates your model:

1. **Review in Fusion 360** - Check dimensions and features
2. **Test fit** - Verify component clearances
3. **Refine** - Ask AI to adjust anything
4. **Export** - Get STEP (for editing) and STL (for printing)
5. **Fabricate** - 3D print, CNC, or send to manufacturer

## More Resources

- **Full Guide**: [PROP_REPLICA_GUIDE.md](PROP_REPLICA_GUIDE.md)
- **Tool Reference**: [README.md](README.md#-available-tools)
- **Example Prompts**: [MCP_Server.py](Server/MCP_Server.py) (search for `@mcp.prompt()`)

## Need Specific Help?

### "How do I add RGB lighting channels?"
```
"Add recessed channels on [location] for RGB LED strips, 1.2cm wide, 0.5cm deep"
```

### "How do I make panels removable?"
```
"Add screw mounting points at corners of [panel name], with alignment pins"
```

### "How do I add a window?"
```
"Create a window cutout on [panel], [dimensions], with mounting lip for acrylic"
```

### "How do I split this for printing?"
```
"This part is too large for my print bed. Can you split it into [2/3/4] sections with alignment features?"
```

---

**Ready to create? Start Fusion 360, run the MCP server, and let the AI guide you!** 🚀
