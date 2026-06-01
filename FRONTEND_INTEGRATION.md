# Frontend Integration Guide for ARC Export

This guide explains how to integrate the ARC export functionality into your frontend application.

## 📁 Components Available

### 1. `ArcExportPanel.tsx`
**Purpose**: Single file ARC export with preview

**Usage**:
```typescript
import ArcExportPanel from './components/ArcExportPanel';

<ArcExportPanel onExportComplete={(filename) => {
  console.log(`Exported: ${filename}`);
}} />
```

**Features**:
- File upload (Schema.org JSON)
- Template selection (auto or manual)
- Preview functionality
- Download ARC file
- Validation feedback

### 2. `ArcBatchProcessor.tsx`
**Purpose**: Batch processing of multiple datasets

**Usage**:
```typescript
import ArcBatchProcessor from './components/ArcBatchProcessor';

<ArcBatchProcessor onBatchComplete={(filename) => {
  console.log(`Batch exported: ${filename}`);
}} />
```

**Features**:
- ZIP file upload
- Batch preview (shows all files)
- Batch download (single ZIP)
- Template selection for all files

### 3. `ArcTemplateSelector.tsx`
**Purpose**: Smart template selection with auto-recommendation

**Usage**:
```typescript
import ArcTemplateSelector from './components/ArcTemplateSelector';

<ArcTemplateSelector 
  file={file}
  value={template}
  onChange={setTemplate}
/>
```

**Features**:
- Auto-detects best template
- Shows recommendation reason
- Handles loading states

## 🔌 API Integration

### Available Endpoints

#### Single File Export
```typescript
import { convertToArc } from './api/client';

const result = await convertToArc(
  file,           // File object
  'schema_org',    // Source format
  'auto',          // Template ID (or 'auto')
  true             // Preview mode
);

// result contains:
// - arcContent: string (ARC JSON-LD)
// - validation: ArcValidationResult
// - filename: string
```

#### Batch Export
```typescript
import { convertBatchToArc } from './api/client';

// Preview mode (returns array of results)
const previewResults = await convertBatchToArc(
  zipFile,        // File object (ZIP)
  'auto',          // Template ID
  true             // Preview mode
);

// Download mode (returns Blob)
const zipBlob = await convertBatchToArc(
  zipFile,        // File object (ZIP)
  'auto',          // Template ID
  false            // Download mode
);

// Create download link
const url = URL.createObjectURL(zipBlob);
const a = document.createElement('a');
a.href = url;
a.download = 'arc_export_batch.zip';
a.click();
```

#### Template Recommendation
```typescript
import { getArcTemplateRecommendation } from './api/client';

const { recommendedTemplate, reason } = await getArcTemplateRecommendation(file);
// Use recommendedTemplate for auto-selection
```

## 🎨 Styling

The components use the following styling approach:

### Colors
- **Primary**: `bg-emerald-600`, `text-white` (buttons)
- **Secondary**: `bg-white`, `border-slate-300` (inputs)
- **Success**: `text-emerald-700`, `bg-emerald-50`
- **Warning**: `text-amber-700`, `bg-amber-50`
- **Error**: `text-red-600`, `bg-red-50`

### Spacing
- `space-y-6` between sections
- `p-4` or `p-8` for containers
- `mb-2` or `mb-4` for labels

### Icons
- Uses `lucide-react` icons
- Size: `w-4 h-4` for buttons, `w-5 h-5` for status

## 📦 State Management

### Recommended Approach

```typescript
import { useState } from 'react';

function ArcExportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [template, setTemplate] = useState<string>('auto');
  const [isProcessing, setIsProcessing] = useState(false);
  const [previewData, setPreviewData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Handle file upload
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
    }
  };

  // Handle export
  const handleExport = async () => {
    if (!file) return;
    
    setIsProcessing(true);
    try {
      const result = await convertToArc(file, 'schema_org', template, false);
      // Handle download
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    // Render components with state
  );
}
```

## 🚀 Deployment

### Prerequisites
- Node.js 18+
- React 18+
- TypeScript 4.9+

### Installation
```bash
npm install lucide-react
npm install @tanstack/react-query  # For API client
```

### Environment Variables
No special environment variables needed for frontend.

### Building
```bash
npm run build
```

### Running
```bash
npm run dev
```

## 🔍 Testing

### Test Files
Create test files in `__tests__/` directory:

```typescript
// __tests__/ArcExportPanel.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import ArcExportPanel from '../components/ArcExportPanel';

describe('ArcExportPanel', () => {
  it('should render file upload', () => {
    render(<ArcExportPanel />);
    expect(screen.getByText('Upload Schema.org JSON File')).toBeInTheDocument();
  });
});
```

### Mock API
```typescript
// __mocks__/api.ts
import { convertToArc } from '../api/client';

jest.mock('../api/client', () => ({
  convertToArc: jest.fn().mockResolvedValue({
    arcContent: '{}',
    validation: { valid: true, errors: [] },
    filename: 'test.json'
  })
}));
```

## 📚 Best Practices

### Error Handling
```typescript
try {
  const result = await convertToArc(file, 'schema_org', template);
  // Success
} catch (err) {
  setError(err instanceof Error ? err.message : 'Unknown error');
  // User-friendly error messages
}
```

### Loading States
```typescript
const [isProcessing, setIsProcessing] = useState(false);

// Show loading spinner during API calls
{isProcessing ? <Loader2 className="animate-spin" /> : <Button />}
```

### Validation
```typescript
if (!previewData.validation.valid) {
  return (
    <div className="text-red-600">
      {previewData.validation.errors.map(error => (
        <div key={error}>{error}</div>
      ))}
    </div>
  );
}
```

## 🎯 Next Steps

1. **Integrate components** into your frontend pages
2. **Connect to backend** (already deployed)
3. **Test thoroughly** with various file types
4. **Deploy to production** when ready

The frontend integration is complete and ready to use! 🎉