import { Component, OnInit, Input } from '@angular/core';
import { ActivatedRoute, Router, Route } from '@angular/router';
import { Subscription } from 'rxjs';
import { GITHUB_URL } from 'src/app/constants';
@Component({
  selector: 'app-mainview',
  template: `
  <div id="navbar">
    <mat-toolbar class="mat-elevation-z6" id="header" color='primary'>
      <span id="title" class="mat-title">
        <button mat-raised-button color="accent" [matMenuTriggerFor]="navMenu">{{title}}</button>
        <mat-menu #navMenu="matMenu">
          <button mat-menu-item color="accent" (click)="navigate(item)" [disabled]="item.activeRoute" *ngFor="let item of navItems">{{item.display}}</button>
        </mat-menu>
      </span>
      <span class="spacer"></span>
      <span id='middle'>
        <mat-button-toggle-group (change)="clickSheet($event)">
          <mat-button-toggle [id]="item.index" [value]="item.name" [checked]="item.sheet.getIsActive()" *ngFor="let item of sheets; trackBy: trackByFunc">
            {{item.name}}
          </mat-button-toggle>
        </mat-button-toggle-group>
      </span>
      <span class="spacer"></span>
      <span>
        <a mat-icon-button disableRipple="true" [href]="GITHUB_URL">
          <fa-icon [icon]="['fab', 'github']" style="display: flex; justify-content: center" size="3x"></fa-icon>
        </a>
      </span>
    </mat-toolbar>
  </div>
  <!-- <span class="spacer"></span> -->
  <ng-content></ng-content>
  `,
  styles: [
    `#navbar {
      display: block;
      position: -webkit-sticky;
      position: sticky;
      top: 0;
      left: 0;
      right: 0;
    }`,
    `#header {
      display: flex;
      /* margin: 0px auto 5px; */
      /* padding: 0px; */
    }`,
    `#header>span {
      align-items: center;
    }`, `.spacer {
      flex: 1 1 auto;
    }`, `#title {
      margin: auto;
    }`
  ]
})
export class MainviewComponent implements OnInit {

  public readonly GITHUB_URL = GITHUB_URL;

  title?: string = 'Movie Analytics';

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
  private readonly subs: Subscription[] = [];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
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
    sheet.getWorkbook().activateSheetAsync(sheet.getIndex())
      .then(
        setTimeout(() => {
          this.sheets = this.sheets.map(x => x.sheet);
        })
      );
  }

  trackByFunc(_: number, item: Sheet): any {
    return item.index
  }

  navigate(item: any) {
    this.router.navigate(item.path.split('/'));
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
