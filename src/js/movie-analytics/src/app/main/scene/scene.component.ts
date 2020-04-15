import { Component } from '@angular/core';
@Component({
  selector: 'app-main',
  templateUrl: './scene.component.html',
  styleUrls: ['./../viz-pages.css']
})
export class SceneComponent {

  sheetFilter = [
    "Words Spoken In Film",
    "Text Analysis by Character",
    "Network of Characters In Film",
    "Action by Character"
  ];

  public readonly vizOptions: any = {
    hideTabs: true,
    hideToolbar: true,
  };

}
