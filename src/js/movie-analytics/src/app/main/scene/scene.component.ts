import { Component } from '@angular/core';
@Component({
  selector: 'app-main',
  templateUrl: './scene.component.html',
  styleUrls: ['./scene.component.css']
})
export class SceneComponent {

  sheetFilter = [
    "Words Spoken In Film",
    "Text Analysis by Character",
    "Network of Characters In Film",
    "Action by Character"
  ];

  activeSheetName: string = '';

  public readonly vizOptions: any = {
    hideTabs: true,
    hideToolbar: true,
  };

  constructor() { }

}
