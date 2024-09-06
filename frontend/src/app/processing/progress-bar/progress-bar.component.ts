import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';

@Component({
  selector: 'app-progress-bar',
  templateUrl: './progress-bar.component.html',
  styleUrls: ['./progress-bar.component.css'],
})
export class ProgressBarComponent implements OnChanges {
  @Input() progress: number = 0;
  @Input() status: string = 'PENDING';

  statusClass: string = 'pending'; // Initialize with a default class

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['progress'] || changes['status']) {
      this.updateStatusClass();
      console.log(`Progress: ${this.progress}, Status: ${this.status}`); // Combined log
    }
  }

  // Update status class based on the current status
  updateStatusClass(): void {
    switch (this.status) {
      case 'PENDING':
        this.statusClass = 'pending';
        break;
      case 'IN_PROGRESS':
        this.statusClass = 'in-progress';
        break;
      case 'COMPLETED':
        this.statusClass = 'completed';
        break;
      case 'FAILED':
        this.statusClass = 'failed';
        break;
      default:
        this.statusClass = '';
        break;
    }
  }
}
