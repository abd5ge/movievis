import { Component } from '@angular/core';

@Component({
  selector: 'app-analysis-summary',
  templateUrl: './analysis-summary.component.html',
  styleUrls: ['./analysis-summary.component.css']
})
export class AnalysisSummaryComponent {

  sheets: any[] = [];

  public readonly vizOptions: any = {
    hideTabs: true,
    hideToolbar: true,
    onFirstInteractive: this.handleVizLoad.bind(this)
  };

  constructor() { }

  handleVizLoad(e: any): void {
    this.sheets = e.getViz().getWorkbook().getPublishedSheetsInfo();
  }
}
