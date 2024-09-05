import {
  Component,
  Input,
  OnInit,
  OnChanges,
  SimpleChanges,
} from '@angular/core';
import { BackendService } from '../../services/backend.service';

@Component({
  selector: 'app-edit',
  templateUrl: './edit.component.html',
  styleUrls: ['./edit.component.css'],
})
export class EditComponent implements OnInit, OnChanges {
  @Input() fileName!: string;
  @Input() outputType!: string;
  @Input() projectId!: number;

  jsonContent: string = '';
  isJsonValid: boolean = true;

  constructor(private backendService: BackendService) {}

  ngOnInit(): void {
    this.resetJson();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['fileName'] || changes['outputType'] || changes['projectId']) {
      this.resetJson();
    }
  }

  validateJson(): void {
    try {
      JSON.parse(this.jsonContent);
      this.isJsonValid = true;
    } catch (e) {
      this.isJsonValid = false;
    }
  }

submitJson(): void {
  if (this.isJsonValid) {
    const encodedFileName = encodeURIComponent(this.fileName);

    // Parse JSON content to ensure it's sent as a proper object
    const jsonObject = JSON.parse(this.jsonContent);

    this.backendService.updateJsonFile(this.projectId, this.outputType, encodedFileName, jsonObject).subscribe(
      () => alert('JSON updated successfully'),
      (error) => alert('Failed to update JSON: ' + error.message)
    );
  }
}

  resetJson(): void {
    const encodedFileName = encodeURIComponent(this.fileName);
    this.backendService
      .getJsonFile(this.projectId, this.outputType, encodedFileName)
      .subscribe(
        (data) => (this.jsonContent = data),
        (error) => alert('Failed to load JSON: ' + error.message)
      );
  }
}
