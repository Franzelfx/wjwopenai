import {
  Component,
  OnInit,
  OnDestroy,
  ChangeDetectorRef,
  NgZone,
  ElementRef,
  ViewChild,
  HostListener,
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
  @ViewChild('processingContainer', { static: true }) containerRef!: ElementRef;

  projectId: number = 0;
  progress: number = 0;
  status: string = 'pending';
  sseSubscription!: Subscription;
  selectedFile: { fileName: string; outputType: string } | null = null;

  // Resizable pane widths
  paneWidths: number[] = [280, 320];
  private isResizing = false;
  private resizeIndex = 0;
  private startX = 0;
  private startWidths: number[] = [];
  private minPaneWidth = 200;
  private maxPaneWidth = 600;

  constructor(
    private route: ActivatedRoute,
    private backendService: BackendService,
    private cdr: ChangeDetectorRef,
    private ngZone: NgZone
  ) {
    // Load saved widths from localStorage
    const savedWidths = localStorage.getItem('processingPaneWidths');
    if (savedWidths) {
      try {
        this.paneWidths = JSON.parse(savedWidths);
      } catch { }
    }
  }

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

  // Resize handling
  startResize(event: MouseEvent, index: number): void {
    event.preventDefault();
    this.isResizing = true;
    this.resizeIndex = index;
    this.startX = event.clientX;
    this.startWidths = [...this.paneWidths];
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }

  @HostListener('document:mousemove', ['$event'])
  onMouseMove(event: MouseEvent): void {
    if (!this.isResizing) return;

    const deltaX = event.clientX - this.startX;
    const newWidth = Math.min(
      this.maxPaneWidth,
      Math.max(this.minPaneWidth, this.startWidths[this.resizeIndex] + deltaX)
    );

    this.paneWidths[this.resizeIndex] = newWidth;
    this.cdr.detectChanges();
  }

  @HostListener('document:mouseup')
  onMouseUp(): void {
    if (this.isResizing) {
      this.isResizing = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      // Save to localStorage
      localStorage.setItem('processingPaneWidths', JSON.stringify(this.paneWidths));
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
