import { Component } from '@angular/core';

@Component({
  selector: 'app-analysis-summary',
  templateUrl: './analysis-summary.component.html',
  styleUrls: ['./../viz-pages.css']
})
export class AnalysisSummaryComponent {

  sheetFilter = [
    "% Lines Spoken By Gender",
    "Revenue by Decade",
    "# of Lines by Race"
  ];

  public readonly vizOptions: any = {
    hideTabs: true,
    hideToolbar: true,
  };

}
