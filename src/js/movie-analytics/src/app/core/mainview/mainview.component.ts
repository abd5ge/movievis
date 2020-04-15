import { Component, OnInit, Input, Output, EventEmitter, ViewChild, ContentChild, OnDestroy, AfterViewInit } from '@angular/core';
import { ActivatedRoute, Router, Route } from '@angular/router';
import { Subscription } from 'rxjs';
import { GITHUB_URL } from 'src/app/constants';
import { TableauDirective } from '../tableau.directive';
@Component({
  selector: 'app-mainview',
  templateUrl: 'mainview.component.html',
  styleUrls: ['mainview.component.css']
})
export class MainviewComponent implements OnInit, AfterViewInit, OnDestroy {

  public readonly GITHUB_URL = GITHUB_URL;

  @ContentChild(TableauDirective) tb: TableauDirective;

  title?= 'Movie Analytics';

  @Input() showTitle = true;

  @Input() showSideNav = true;

  @Input() filterTo: string[] = [];

  private _sheets: Sheet[] = [];
  @Input()
  set sheets(sheets: any[]) {

    let tmp = (sheets || []).filter(x => !x.getIsHidden());
    if (this.filterTo != null && this.filterTo.length > 0) {
      tmp = tmp.filter(x => this.filterTo.includes(x.getName()));
    }

    this._sheets = tmp.map(x => ({
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
    if (this.tb) {
      this.subs.push(this.tb.onFirstInteractive.subscribe((e: any) => {
        this.sheets = this.tb.viz.getWorkbook().getPublishedSheetsInfo();
      }))
      this.subs.push(this.tb.onTabSwitch.subscribe((e: any) => {
        this.sheets = this.sheets.map(x => x.sheet);
      }));
    }
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
  isHidden: boolean;
  isActive: boolean;
  sheet: any;
}
