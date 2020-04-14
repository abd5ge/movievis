import { Component, OnInit, Input, Output, EventEmitter, ViewChild, ContentChild, OnDestroy, AfterViewInit } from '@angular/core';
import { ActivatedRoute, Router, Route } from '@angular/router';
import { Subscription } from 'rxjs';
import { GITHUB_URL } from 'src/app/constants';
import { TableauDirective } from '../tableau.directive';
@Component({
  selector: 'app-mainview',
  template: `
  <div id="navbar">
    <mat-toolbar class="mat-elevation-z6" id="header" color='primary'>
      <button mat-button style="padding: 0" (click)="router.navigate(['landing'])"><img src="movievislogo.png" alt="image" height="36" width="200"></button>
      <span class="spacer"></span>
      <span >
          <button mat-button
          (click)="navigate(item)"
          *ngFor="let item of navItems">{{item.display}}</button>
      </span>
    </mat-toolbar>
  </div>
  <div *ngIf="showTitle" id="titlebar">
    <mat-toolbar color='primary'>
      <span id="title" class="mat-title">
        <h2 mat-h2>{{title}}</h2>
      </span>
    </mat-toolbar>
  </div>
  <mat-sidenav-container autosize>
    <mat-sidenav mode="side" [opened]="showSideNav">
      <mat-button-toggle-group (change)="clickSheet($event)" [vertical]="true">
        <mat-button-toggle [id]="item.index" [value]="item.name" [checked]="item.isActive" *ngFor="let item of sheets; trackBy: trackByFunc">
          {{item.name}}
        </mat-button-toggle>
      </mat-button-toggle-group>
    </mat-sidenav>
    <mat-sidenav-content>
      <ng-content></ng-content>
    </mat-sidenav-content>
  </mat-sidenav-container>
  <div id="footer">
    <mat-toolbar color='primary'>
      <span class="spacer"></span>
      <span>
        <a mat-icon-button disableRipple="true" [href]="GITHUB_URL">
          <fa-icon [icon]="['fab', 'github']" style="display: flex; justify-content: center" size="3x"></fa-icon>
        </a>
      </span>
    </mat-toolbar>
  </div>
  `,
  styles: [
    `#navbar {
      display: block;
      position: -webkit-sticky;
      position: sticky;
      top: 0;
      left: 0;
      right: 0;
      z-index: 9999;
    }`,
    `#header {
      display: flex;
    }`,
    `#header>span {
      align-items: center;
    }`, `.spacer {
      flex: 1 1 auto;
    }`, `#title {
      margin: auto 0;
    }`
  ]
})
export class MainviewComponent implements OnInit, AfterViewInit, OnDestroy {

  public readonly GITHUB_URL = GITHUB_URL;

  @ContentChild(TableauDirective) tb: TableauDirective;

  title?: string = 'Movie Analytics';

  @Input() showTitle: boolean = true;

  @Input() showSideNav: boolean = true;

  @Output() activeSheetName: EventEmitter<string> = new EventEmitter<string>();

  private _sheets: Sheet[] = [];
  @Input()
  set sheets(sheets: any[]) {
    this._sheets = (sheets || []).filter(x => !x.getIsHidden()).map(x => ({
      name: x.getName(),
      index: x.getIndex(),
      workbook: x.getWorkbook(),
      isHidden: x.getIsHidden(),
      isActive: x.getIsActive(),
      sheet: x
    }));
    const activeSheet = this._sheets.find(s => s.sheet.getIsActive());
    if(activeSheet) {
      this.activeSheetName.emit(activeSheet.name);
    }
  }
  get sheets() {
    return this._sheets;
  }

  @Input() set routes(routes: Route[]) {
    this.navItems = this.routes.filter(x => x.data && x.data.show).map(r => ({
      path: r.path,
      display: r.data && r.data.display as string,
      activeRoute: false
    }));
  }

  navItems: Array<{ path?: string, display?: string, activeRoute: boolean }> = [];
  private subs: Subscription[] = [];

  constructor(
    private route: ActivatedRoute,
    public router: Router,
  ) { }


  ngOnInit(): void {
    this.navItems = this.getRoutesFlatten('', this.router.config)
      .filter(r => r.route.data && r.route.data.show)
      .map(r => ({
        path: r.fullpath,
        display: r.route.data && r.route.data.display,
        activeRoute: false
      }));
    this.subs.push(this.route.url.subscribe(segs => {
      const path = '/' + segs.join('/');
      const item = this.navItems.find(n => path == n.path);
      if (item) {
        item.activeRoute = true;
        this.title = item.display;
      }
    }));
  }

  ngAfterViewInit(): void {
    this.subs.push(this.tb.onFirstInteractive.subscribe((e: any) => {
      this.sheets = this.tb.viz.getWorkbook().getPublishedSheetsInfo();
    }))
    this.subs.push(this.tb.onTabSwitch.subscribe((e: any) => {
      this.activeSheetName.emit(e.getNewSheetName());
      this.sheets = this.sheets.map(x => x.sheet);
    }));
  }

  private getRoutesFlatten(parent_path: string, routes: Route[]): { fullpath: string, route: Route }[] {
    let ret: { fullpath: string, route: Route }[] = [];
    routes.forEach(r => {
      const path = parent_path + '/' + r.path;
      ret.push({
        fullpath: path,
        route: r
      });
      if (r.children) {
        ret = ret.concat(this.getRoutesFlatten(path, r.children));
      }
    })
    return ret;
  }

  clickSheet(e: { value: string }): void {
    const sheet: any = this.sheets.find(x => x.name == e.value).sheet;
    sheet.getWorkbook().activateSheetAsync(sheet.getIndex());
  }

  trackByFunc(_: number, item: Sheet): any {
    return item.index
  }

  navigate(item: any) {
    this.router.navigate(item.path.split('/'));
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
    this.subs = [];
  }
}

interface Sheet {
  name: string;
  index: number;
  workbook: any;
  // url: string;
  // sheetType: string;
  isHidden: boolean;
  isActive: boolean;
  sheet: any;
}
