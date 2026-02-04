import {
  Component,
  Input,
  OnInit,
  OnChanges,
  SimpleChanges,
  HostListener,
  ElementRef,
} from '@angular/core';
import { FormControl } from '@angular/forms';
import { firstValueFrom } from 'rxjs';              // ← NEW
import { BackendService } from '../../services/backend.service';

@Component({
  selector: 'app-edit',
  templateUrl: './edit.component.html',
  styleUrls: ['./edit.component.css'],
})
export class EditComponent implements OnInit, OnChanges {
  /* ── inputs from parent list/tree ─────────────── */
  @Input() fileName!: string;
  @Input() outputType!: string;   // 'success' | 'fail'
  @Input() projectId!: number;

  /* ── editor + preview state ───────────────────── */
  jsonControl = new FormControl('');
  imageUrl: string | null = null;
  isJsonValid = true;
  isLoading = false;
  isZoomed = false;
  showSaveSuccess = false;

  /* ── vertical resize state ───────────────────── */
  imageFlex = 1;
  jsonFlex = 1;
  private isResizing = false;
  private startY = 0;
  private startImageFlex = 1;
  private startJsonFlex = 1;

  private readonly imgExts = ['png', 'jpeg', 'jpg', 'tif', 'tiff'];

  constructor(
    private backend: BackendService,
    private elementRef: ElementRef
  ) {
    // Load saved proportions
    const saved = localStorage.getItem('editPaneSplit');
    if (saved) {
      try {
        const { image, json } = JSON.parse(saved);
        this.imageFlex = image;
        this.jsonFlex = json;
      } catch { }
    }
  }

  /* ─────────────────────────────────────────────── */
  ngOnInit(): void {
    this.resetJson();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['fileName'] || changes['outputType'] || changes['projectId']) {
      this.isZoomed = false;
      this.resetJson();
    }
  }

  toggleZoom(): void {
    this.isZoomed = !this.isZoomed;
  }

  /* ── vertical resize handling ─────────────────── */
  startVerticalResize(event: MouseEvent): void {
    event.preventDefault();
    this.isResizing = true;
    this.startY = event.clientY;
    this.startImageFlex = this.imageFlex;
    this.startJsonFlex = this.jsonFlex;
    document.body.style.cursor = 'row-resize';
    document.body.style.userSelect = 'none';
  }

  @HostListener('document:mousemove', ['$event'])
  onMouseMove(event: MouseEvent): void {
    if (!this.isResizing) return;

    const container = this.elementRef.nativeElement.querySelector('.edit-wrapper');
    if (!container) return;

    const containerHeight = container.clientHeight - 80; // subtract headers/action bar
    const deltaY = event.clientY - this.startY;
    const totalFlex = this.startImageFlex + this.startJsonFlex;
    const deltaFlex = (deltaY / containerHeight) * totalFlex * 2;

    const newImageFlex = Math.max(0.2, Math.min(2.5, this.startImageFlex + deltaFlex));
    const newJsonFlex = Math.max(0.2, Math.min(2.5, this.startJsonFlex - deltaFlex));

    this.imageFlex = newImageFlex;
    this.jsonFlex = newJsonFlex;
  }

  @HostListener('document:mouseup')
  onMouseUp(): void {
    if (this.isResizing) {
      this.isResizing = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      // Save to localStorage
      localStorage.setItem('editPaneSplit', JSON.stringify({
        image: this.imageFlex,
        json: this.jsonFlex
      }));
    }
  }

  /* ─────────────────────────────────────────────── */
  onEditorInput(): void {
    const raw = this.jsonControl.value ?? '';
    try {
      JSON.parse(raw);
      this.isJsonValid = true;
    } catch {
      this.isJsonValid = false;
    }
  }

  submit(): void {
    if (!this.isJsonValid) { return; }

    const jsonContent = this.jsonControl.value!;

    this.backend.updateJsonFile(
      this.projectId,
      this.outputType,
      encodeURIComponent(this.fileName),
      jsonContent  // Pass the raw JSON string, not parsed object
    ).subscribe({
      next: () => {
        // Show a nicer notification instead of alert
        this.showSaveSuccess = true;
        setTimeout(() => this.showSaveSuccess = false, 3000);
      },
      error: (err) => {
        console.error('Failed to update JSON:', err);
        alert('Fehler beim Speichern: ' + (err.error?.detail || err.message));
      },
    });
  }

  /* ─────────────────────────────────────────────── */
  resetJson(): void {
    if (!this.fileName) { return; }

    this.isLoading = true;
    const encoded = encodeURIComponent(this.fileName);

    /* fetch & pretty-print JSON */
    this.backend.getJsonFile(this.projectId, this.outputType, encoded)
      .subscribe({
        next: (txt: string) => {
          try { txt = JSON.stringify(JSON.parse(txt), null, 2); } catch { }
          this.jsonControl.setValue(txt);
          this.isJsonValid = true;
        },
        error: (err) => alert('Failed to load JSON: ' + err.message),
        complete: () => (this.isLoading = false),
      });

    /* fetch preview image */
    this.loadCorrespondingImage(this.fileName);
  }

  /** sequentially try png → jpeg → … until one responds 200 */
  private async loadCorrespondingImage(originalName: string): Promise<void> {
    // clear previous preview
    if (this.imageUrl) {
      URL.revokeObjectURL(this.imageUrl);
      this.imageUrl = null;
    }

    // Remove .json extension and _invalid suffix to get the original image name
    const base = originalName
      .replace(/\.json$/i, '')
      .replace(/_invalid$/i, '');
    for (const ext of this.imgExts) {
      const encodedImg = encodeURIComponent(`${base}.${ext}`);
      try {
        const blob = await firstValueFrom(
          this.backend.getInputFile(this.projectId, encodedImg)
        );
        this.imageUrl = URL.createObjectURL(blob);
        break;                                 // success: stop trying
      } catch {
        /* ignore 404 and continue */
      }
    }
  }
}
