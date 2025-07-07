// progress-bar.component.ts
import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';

@Component({
  selector: 'app-progress-bar',
  templateUrl: './progress-bar.component.html',
  styleUrls: ['./progress-bar.component.css'],
})
export class ProgressBarComponent implements OnChanges {
  @Input() progress: number = 0;
  @Input() status: string = 'PENDING';

  statusClass: string = 'pending';

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['progress'] || changes['status']) {
      this.updateStatusClass();
      console.log(`Progress: ${this.progress}, Status: ${this.status}`);
    }
  }

  private updateStatusClass(): void {
    // normalize: trim, lowercase, convert spaces/underscores to hyphens
    const key = this.status
      .trim()
      .toLowerCase()
      .replace(/[_\s]+/g, '-'); // e.g. "IN_PROGRESS" -> "in-progress"

    switch (key) {
      case 'pending':
        this.statusClass = 'pending';
        break;
      case 'in-progress':
        this.statusClass = 'in-progress';
        break;
      case 'paused':
        this.statusClass = 'paused';
        break;
      case 'completed':
        this.statusClass = 'completed';
        break;
      case 'failed':
        this.statusClass = 'failed';
        break;
      default:
        this.statusClass = '';
    }
  }
}
