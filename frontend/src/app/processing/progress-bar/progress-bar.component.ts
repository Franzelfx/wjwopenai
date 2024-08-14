import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';

@Component({
  selector: 'app-progress-bar',
  templateUrl: './progress-bar.component.html',
  styleUrls: ['./progress-bar.component.css'],
})
export class ProgressBarComponent implements OnChanges {
  @Input() progress: number = 0;
  @Input() status: string = 'PENDING';

  // Define statusClass based on the current status
  get statusClass(): string {
    switch (this.status) {
      case 'PENDING':
        return 'pending';
      case 'IN_PROGRESS':
        return 'in-progress';
      case 'COMPLETED':
        return 'completed';
      case 'FAILED':
        return 'failed';
      default:
        return '';
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['progress']) {
      console.log('Progress updated:', this.progress);
    }
    if (changes['status']) {
      console.log('Status updated:', this.status);
    }
  }
}
