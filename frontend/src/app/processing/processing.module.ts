import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProcessingComponent } from './processing.component';
import { ProcessingRoutingModule } from './processing-routing.module';
import { MatTreeModule } from '@angular/material/tree';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

@NgModule({
  declarations: [ProcessingComponent],
  imports: [
    CommonModule,
    ProcessingRoutingModule,
    MatTreeModule,
    MatIconModule,
    MatButtonModule,
  ],
})
export class ProcessingModule {}
