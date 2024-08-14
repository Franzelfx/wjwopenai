import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { BackendService } from '../services/backend.service';

@Component({
  selector: 'app-processing',
  templateUrl: './processing.component.html',
  styleUrls: ['./processing.component.css'],
})
export class ProcessingComponent implements OnInit {
  projectId: number = 0;
  progress: number = 0;
  status: string = 'PENDING';

  constructor(
    private route: ActivatedRoute,
    private backendService: BackendService
  ) {}

  ngOnInit(): void {
    console.log('ProcessingComponent initialized');
    this.projectId = +this.route.snapshot.paramMap.get('id')!;
    this.fetchStatus();
  }

  fetchStatus(): void {
    this.backendService.getProcessingStatus(this.projectId).subscribe(
      (statusData) => {
        this.progress = statusData.progress;
        this.status = statusData.status;
      },
      (error) => {
        console.error('Error fetching processing status:', error);
      }
    );
  }
}
