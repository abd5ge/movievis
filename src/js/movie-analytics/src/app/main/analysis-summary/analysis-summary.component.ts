import { Component } from '@angular/core';

@Component({
  selector: 'app-analysis-summary',
  templateUrl: './analysis-summary.component.html',
  styleUrls: ['./analysis-summary.component.css']
})
export class AnalysisSummaryComponent {

  public readonly vizOptions: any = {
    hideTabs: true,
    hideToolbar: true,
  };

  constructor() { }

}
