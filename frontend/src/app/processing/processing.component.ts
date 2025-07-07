import {
  Component,
  OnInit,
  OnDestroy,
  ChangeDetectorRef,
  NgZone,
} from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { BackendService } from '../services/backend.service';
import { Subscription } from 'rxjs';

interface StatusData {
  progress: number;
  status: string;
}

@Component({
  selector: 'app-processing',
  templateUrl: './processing.component.html',
  styleUrls: ['./processing.component.css'],
})
export class ProcessingComponent implements OnInit, OnDestroy {
  projectId: number = 0;
  progress: number = 0;
  status: string = 'pending';
  sseSubscription!: Subscription;
  selectedFile: { fileName: string; outputType: string } | null = null;

  constructor(
    private route: ActivatedRoute,
    private backendService: BackendService,
    private cdr: ChangeDetectorRef,
    private ngZone: NgZone // Inject NgZone
  ) { }

  ngOnInit(): void {
    console.log('ProcessingComponent initialized');
    const projectIdParam = this.route.snapshot.paramMap.get('id');

    if (projectIdParam) {
      this.projectId = +projectIdParam;
      this.listenToProcessingStatus();
    } else {
      console.error('Project ID is missing in the route parameters');
    }
  }

  listenToProcessingStatus(): void {
    this.sseSubscription = this.backendService
      .getProcessingStatusSSE(this.projectId)
      .subscribe(
        (event: MessageEvent) => {
          try {
            const data: StatusData = JSON.parse(event.data);

            // Ensure that the change detection is triggered correctly
            this.ngZone.run(() => {
              this.progress = data.progress;
              this.status = data.status;
              console.log('SSE Update:', data); // Debugging log
            });
          } catch (error) {
            console.error('Error parsing SSE data:', error);
          }
        },
        (error) => {
          // Handle errors and make sure to trigger change detection
          this.ngZone.run(() => {
            console.error('Error receiving SSE:', error);
            this.status = 'FAILED';
          });
        }
      );
  }

  ngOnDestroy(): void {
    if (this.sseSubscription) {
      this.sseSubscription.unsubscribe();
    }
  }

  onFileSelected(event: { fileName: string; outputType: string }): void {
    this.selectedFile = event; // Correctly set the selected file
  }
}
