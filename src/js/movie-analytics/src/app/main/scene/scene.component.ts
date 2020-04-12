import { Component } from '@angular/core';
// import {routes} from './../main-routing-module';
@Component({
  selector: 'app-main',
  templateUrl: './scene.component.html',
  styleUrls: ['./scene.component.css']
})
export class SceneComponent {
  sheets: any[] = [];
  // routes = routes;

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
