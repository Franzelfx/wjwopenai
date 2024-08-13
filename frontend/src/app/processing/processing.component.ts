import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-processing',
  templateUrl: './processing.component.html',
  styleUrls: ['./processing.component.css'],
})
export class ProcessingComponent implements OnInit {
  projectId: number = 0;

  constructor(private route: ActivatedRoute) {}

  ngOnInit(): void {
    console.log('ProcessingComponent initialized');
    this.projectId = +this.route.snapshot.paramMap.get('id')!;
  }
}
