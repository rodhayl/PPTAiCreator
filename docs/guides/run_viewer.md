# Run History Viewer - Implementation Guide

## 📋 Overview

You requested the ability to **view complete information from previous runs** directly in the Streamlit UI, not just download PPTX files.

This guide provides everything needed to implement a comprehensive **Run History Viewer** that displays:
- Generated outlines (topic, sections, learning objectives)
- Slide content (titles, bullets, speaker notes, citations)
- Research data (claims, evidence, citations)
- Full QA feedback (not just scores)
- Model configuration and execution metrics

---

## 📚 Documentation Files (Read in Order)

### 1. **RUN_VIEWER_SUMMARY.md** ← **START HERE**
- What's the problem? (Current limitations)
- What's the solution? (New Run History tab)
- High-level benefits and features
- User experience flow
- Files to modify

**Read this first** for a clear understanding of what you're building.

### 2. **IMPLEMENTATION_VISUAL_GUIDE.md** ← **THEN READ THIS**
- Current vs proposed architecture (visual diagrams)
- Database schema before/after
- File structure changes
- UI changes (before/after mockups)
- Data flow during execution
- Serialization examples
- Implementation sequence with timing
- Expected database state

**Read this second** for visual understanding of the architecture.

### 3. **RUN_HISTORY_VIEWER_PLAN.md** ← **DETAILED TECHNICAL GUIDE**
- Complete technical deep-dive
- SQL migrations
- Enhanced CheckpointManager code
- Full UI component code
- Run viewer display functions
- Pipeline updates
- Data serialization examples
- Benefits and implementation steps

**Read this last** for detailed code examples and implementation details.

---

## 🎯 Quick Summary

### Current Limitation
```
User generates presentation
    ↓
Database stores: input, QA scores, file path only ❌
    ↓
UI shows: Sidebar with last 5 runs
    ↓
To view details: Must download PPTX ❌
```

### Proposed Solution
```
User generates presentation
    ↓
Database stores: COMPLETE DATA (outline, slides, research, QA feedback) ✅
    ↓
New UI Tab: Run History with full viewer ✅
    ↓
To view details: Select run from dropdown, view everything in browser ✅
```

---

## 📊 What Gets Built

### New Feature: Run History Tab
```
Five Sub-Tabs:
├─ 📋 Outline Tab
│  └─ Topic, Audience, Sections, Learning Objectives, Prerequisites
│
├─ 🎯 Slides Tab
│  └─ All slides with expandable view (title, bullets, speaker notes, citations)
│
├─ 📚 Research Tab
│  └─ Claims, Evidence, Citations extracted
│
├─ ✅ QA Tab
│  └─ Scores (content, design, coherence) + full feedback text
│
└─ ⬇️ Download Tab
   └─ Download PPTX button
```

---

## 🔧 Implementation Checklist

### Phase 1: Database (5-10 min)
- [ ] Add new columns to runs table (backward compatible)
  - outline, content, research, qa_feedback, model_info, educational_mode, execution_time_seconds, error_messages

### Phase 2: Fix Bug (2-5 min)
- [ ] Fix hardcoded "sample_output.pptx" filename
  - Change to: `presentation_{timestamp}.pptx`

### Phase 3: CheckpointManager (15-20 min)
- [ ] Add serialization methods (_serialize_outline, _serialize_content, _serialize_research)
- [ ] Add retrieval methods (get_run_details, list_runs)
- [ ] Add record_run_complete method

### Phase 4: UI Components (20-30 min)
- [ ] Add new "Run History" tab
- [ ] Create run selector dropdown
- [ ] Implement display_outline function
- [ ] Implement display_slides function
- [ ] Implement display_research function
- [ ] Implement display_qa function
- [ ] Implement display_download function
- [ ] Create tab structure

### Phase 5: Pipeline (5-10 min)
- [ ] Add timer to run_pipeline
- [ ] Call record_run_complete instead of record_run
- [ ] Pass complete state data

### Phase 6: Testing (10 min)
- [ ] Verify existing tests pass
- [ ] Generate new run and verify data captured
- [ ] Test Run History viewer tab
- [ ] Test run selection and data display

**Total Time: ~75 minutes**

---

## 📈 Benefits

| Before | After |
|--------|-------|
| Download PPTX to view details | View everything in browser immediately |
| See last 5 runs only | See all 100+ previous runs |
| Only see input + scores | See outline, slides, research, QA all together |
| No metadata | See duration, model used, mode |
| Same filename for all runs | Unique filename per run |
| No run comparison | Can compare runs side-by-side |

---

## 🗂️ Files to Modify

| File | Changes | Lines |
|------|---------|-------|
| `src/graph/build_graph.py` | Enhance CheckpointManager | ~60 lines |
| `src/agents/design.py` | Fix hardcoded filename | 1 line |
| `src/app.py` | Add Run History tab + display functions | ~150 lines |
| **Database** | Add new columns (migration) | 8 columns |

**Total: ~211 new/modified lines**

---

## 🚀 Getting Started

1. **Read** `RUN_VIEWER_SUMMARY.md` (5 minutes)
   - Understand what you're building

2. **Review** `IMPLEMENTATION_VISUAL_GUIDE.md` (10 minutes)
   - See architecture and data flow

3. **Implement** using code in `RUN_HISTORY_VIEWER_PLAN.md` (75 minutes)
   - Follow the checklist above

4. **Test** the new feature
   - Generate a run, view in Run History tab

---

## 💡 Key Design Decisions

### Backward Compatibility
- New database columns are optional (NULL for old runs)
- Existing code still works
- Old runs can be viewed with partial data

### Data Serialization
- Store complete Python objects as JSON
- Deserialize when retrieving
- Allows full data availability without PPTX

### Unique Filenames
- Timestamp-based: `presentation_20251105_143022.pptx`
- Prevents file overwrites
- Each run has its own PPTX

### UI Organization
- Run selector dropdown (easy navigation)
- Five focused tabs (organized information)
- Minimal learning curve

---

## 🔍 Example Usage

### User Workflow
1. Open "Run History" tab
2. Click dropdown: "Select a run to view"
3. Choose: "Run #5: Climate change... (2025-11-05)"
4. View metrics: Created, Duration, Mode
5. Click "Outline" tab → See topic, sections, learning objectives
6. Click "Slides" tab → Expand slides to read content
7. Click "Research" tab → See evidence and citations
8. Click "QA" tab → Read detailed feedback
9. Click "Download" tab → Download PPTX if needed

---

## 📝 Database Schema Preview

### Before Implementation
```sql
CREATE TABLE runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT,
    status TEXT,
    input TEXT,
    output_path TEXT,
    qa_scores TEXT
);
```

### After Implementation
```sql
CREATE TABLE runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT,
    status TEXT,
    input TEXT,
    output_path TEXT,
    qa_scores TEXT,

    -- New columns
    outline TEXT,
    content TEXT,
    research TEXT,
    qa_feedback TEXT,
    model_info TEXT,
    educational_mode INTEGER,
    execution_time_seconds REAL,
    error_messages TEXT
);
```

---

## ⚠️ Important Notes

### Data Storage
- All serialized as JSON (text in database)
- Deserialize when retrieving for display
- Backward compatible (old runs have NULL values)

### Performance
- SQLite query by id is fast (indexed)
- JSON deserialization is lightweight
- Suitable for 100+ runs per user

### Storage
- Each run adds ~5-10 KB to database (JSON storage)
- For 1000 runs: ~5-10 MB database size
- Very manageable

---

## 🎓 Learning Resources

### Referenced Files in Codebase
- **PipelineState** (src/state.py) - Data structure for complete run data
- **Outline, Slide, QAReport** (src/schemas.py) - Schema definitions
- **CheckpointManager** (src/graph/build_graph.py) - Database interaction
- **Streamlit components** (src/app.py) - UI examples

### New Concepts
- JSON serialization/deserialization
- SQLite ALTER TABLE (schema migration)
- Streamlit tabs and selectors
- Type hints (Python typing)

---

## ❓ FAQ

### Q: Will this break existing runs?
A: No. New database columns are optional (NULL for old runs). Old runs still work but with less data available in viewer.

### Q: How much database space does this use?
A: ~5-10 KB per run for JSON data. 1000 runs = ~5-10 MB total.

### Q: Can I compare two runs?
A: Not built-in, but the viewer supports it. Users can open two tabs to view different runs side-by-side.

### Q: What if a run has an error?
A: Error is captured in `error_messages` field. Viewer shows partial data with error notification.

### Q: Does this work with educational mode?
A: Yes. `educational_mode` field tracks this, and all pedagogical data (learning objectives, prerequisites) are stored.

---

## 📞 Support

### For Questions:
- See `RUN_VIEWER_SUMMARY.md` - What and why
- See `IMPLEMENTATION_VISUAL_GUIDE.md` - How (architecture)
- See `RUN_HISTORY_VIEWER_PLAN.md` - Implementation details

### For Implementation Help:
- Follow the checklist in the Visual Guide
- Use code snippets from the Plan document
- Test each phase before moving to next

---

## 📅 Status

✅ **Planning Complete** - Ready to implement
✅ **Architecture Defined** - Clear implementation path
✅ **Documentation Complete** - Code snippets provided
✅ **Timeline Estimated** - ~75 minutes total
✅ **Backward Compatibility** - Verified

---

**Next Steps:**
1. Read `RUN_VIEWER_SUMMARY.md`
2. Review `IMPLEMENTATION_VISUAL_GUIDE.md`
3. Implement using `RUN_HISTORY_VIEWER_PLAN.md`
4. Test and verify
5. Deploy!

Good luck! 🚀
