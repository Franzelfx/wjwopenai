import {
  Component,
  Input,
  OnInit,
  OnChanges,
  SimpleChanges,
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

  private readonly imgExts = ['png', 'jpeg', 'jpg', 'tif', 'tiff'];

  constructor(private backend: BackendService) { }

  /* ─────────────────────────────────────────────── */
  ngOnInit(): void {
    this.resetJson();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['fileName'] || changes['outputType'] || changes['projectId']) {
      this.resetJson();
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

    this.backend.updateJsonFile(
      this.projectId,
      this.outputType,
      encodeURIComponent(this.fileName),
      JSON.parse(this.jsonControl.value!)
    ).subscribe({
      next: () => alert('JSON updated successfully'),
      error: (err) => alert('Failed to update JSON: ' + err.message),
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

    const base = originalName.replace(/\\.json$/i, '');
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
