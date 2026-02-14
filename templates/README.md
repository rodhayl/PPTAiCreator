# PPTAgent Templates Directory

This directory contains PowerPoint template files used by the PPTAgent template system.

---

## Directory Structure

```
templates/
├── default.pptx              # Clean & simple template (general purpose)
├── professional.pptx         # Corporate blue template (business)
├── academic.pptx             # Research theme template (academic)
├── creative.pptx             # Modern colorful template (marketing)
├── minimalist.pptx           # Ultra-clean template (minimalist)
├── custom/                   # User-uploaded custom templates
│   └── (your templates here)
└── README.md                 # This file
```

---

## Built-in Templates

### 1. default.pptx - Clean & Simple
- **Style:** White background, sans-serif fonts, high contrast
- **Best For:** General purpose, professional presentations
- **Features:** Minimal decorations, focus on content

### 2. professional.pptx - Corporate Style
- **Style:** Blue gradient header, corporate colors
- **Best For:** Business presentations, quarterly reports
- **Features:** Professional fonts, clean layout

### 3. academic.pptx - Research Theme
- **Style:** Clean white, serif fonts, formal design
- **Best For:** Academic talks, research presentations
- **Features:** Citation-friendly layout, section numbering

### 4. creative.pptx - Modern & Colorful
- **Style:** Vibrant backgrounds, modern fonts, geometric shapes
- **Best For:** Marketing, startups, pitches
- **Features:** Bright color palette, dynamic layouts

### 5. minimalist.pptx - Ultra-Clean
- **Style:** Black & white only, maximum white space
- **Best For:** Minimalist presentations, zen-style talks
- **Features:** Ultra-simple design, content-focused

---

## Creating Templates

If these files don't exist yet, create them by running:

```bash
python scripts/create_default_templates.py
```

This will generate all 5 default templates in this directory.

---

## Using Templates

### In GUI

1. Start the application: `start.bat`
2. Navigate to "🚀 Quick Generate" tab
3. Check "📐 Use Design Template"
4. Select template from dropdown
5. Generate your presentation!

### Programmatically

```python
from src.tools.pptx_builder import build_presentation

build_presentation(
    slides=my_slides,
    references=my_references,
    output_path="output.pptx",
    template_name="professional"  # Use template
)
```

---

## Uploading Custom Templates

### Via GUI (Recommended)

1. Open http://localhost:8501
2. Go to "⚙️ Settings" tab
3. Scroll to "5️⃣ Presentation Templates"
4. Click "Choose a PowerPoint file (.pptx)"
5. Select your template
6. Click "📤 Upload Template"
7. Template will be saved to `templates/custom/`

### Manual Upload

1. Create your template in PowerPoint
2. Save as `.pptx` file
3. Copy to `templates/custom/`
4. Restart application to recognize new template

---

## Template Requirements

### Minimum Requirements

Your template MUST have:
- ✅ At least 1 slide layout
- ✅ Layout 0 with title placeholder (for title slide)
- ✅ Content layout with body placeholder (for bullets)

### Recommended Structure

| Layout | Type | Purpose |
|--------|------|---------|
| 0 | Title Slide | Presentation title page |
| 1 | Section Header | Section dividers |
| 2 | Content | Main content slides |
| 3 | Two Column | Special layouts |
| 5 | References | Citations list |

### Creating Valid Templates

1. **Open PowerPoint**
2. **View → Slide Master**
3. **Design your layouts** with placeholders (not text boxes!)
4. **Use Insert → Placeholder** for all text areas
5. **Exit Slide Master**
6. **Delete example slides**
7. **Save as .pptx**

**IMPORTANT:** Use PowerPoint placeholders, NOT text boxes!

---

## Template Validation

When you upload a template, it will be automatically validated. The system checks:

✅ File is valid .pptx
✅ Has at least 1 layout
✅ Layout 0 has title placeholder
✅ Content layout has body placeholder

If validation fails, you'll see an error message explaining what's wrong.

---

## Managing Templates

### List Templates

```python
from src.tools.template_manager import TemplateManager

tm = TemplateManager()
templates = tm.list_templates()
print(templates)
# ['default', 'professional', 'academic', 'creative', 'minimalist', 'custom/my_template']
```

### Delete Custom Template

Via GUI:
1. Settings → Presentation Templates
2. Find your template in the list
3. Click "🗑 Delete" button
4. Confirm deletion

**Note:** Built-in templates cannot be deleted (only custom templates).

---

## Troubleshooting

### No templates showing

**Solution:**
```bash
python scripts/create_default_templates.py
```

### Template upload fails

**Possible causes:**
- File is not valid .pptx
- Template doesn't have required layouts
- Template has no placeholders (only text boxes)
- File is corrupted

**Fix:** Open in PowerPoint, verify placeholders, re-save.

### Content not filling template

**Cause:** Using text boxes instead of placeholders

**Fix:** In PowerPoint:
1. View → Slide Master
2. Delete text boxes
3. Insert → Placeholder → Text
4. Re-save template

---

## Best Practices

### DO:
✅ Use native PowerPoint placeholders
✅ Keep layouts simple
✅ Test with small presentation first
✅ Document your template structure
✅ Use web-safe fonts
✅ Include multiple layout options

### DON'T:
❌ Use text boxes instead of placeholders
❌ Create overly complex layouts
❌ Hardcode content in template
❌ Use too many different fonts
❌ Lock placeholders unnecessarily
❌ Include example content

---

## Template Specifications

### File Format
- Format: `.pptx` (PowerPoint 2007+)
- Not supported: `.ppt` (old format)
- Compatible: `.potx` (saved as .pptx)

### Size Guidelines
- Typical size: 25-35 KB
- Maximum recommended: 5 MB
- Larger files may slow uploads

### Slide Size
- Default: 10" × 7.5" (16:9)
- Also supported: 4:3 aspect ratio
- Custom sizes supported

---

## Support

### Documentation
- **Quick Start:** `../docs/archive/reports/TEMPLATE_QUICK_START.md`
- **User Guide:** `../docs/archive/reports/TEMPLATE_USER_GUIDE.md`
- **Architecture:** `../docs/archive/reports/TEMPLATE_SYSTEM_DESIGN.md`
- **Implementation:** `../docs/archive/reports/TEMPLATE_IMPLEMENTATION_COMPLETE.md`

### Testing
```bash
python -m pytest tests/test_template_integration.py -q
```

### Getting Help
- Check documentation files above
- Verify template requirements
- Test with built-in templates first
- Review error messages carefully

---

## Version History

**v1.0 (2025-11-05)**
- Initial release with 5 built-in templates
- Upload/delete functionality
- GUI integration
- Validation system

---

**Happy templating!** 🎨

For more information, see the complete documentation in the project root.
