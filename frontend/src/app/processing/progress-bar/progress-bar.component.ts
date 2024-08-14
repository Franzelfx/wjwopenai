import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-progress-bar',
  templateUrl: './progress-bar.component.html',
  styleUrls: ['./progress-bar.component.css'],
})
export class ProgressBarComponent {
  @Input() progress: number = 0;
  @Input() status: string = 'PENDING';

  constructor() {
    console.log(
      'ProgressBarComponent initialized with progress:',
      this.progress,
      'and status:',
      this.status
    );
  }
}
