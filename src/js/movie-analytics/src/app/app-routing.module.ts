import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { MainModule } from './main/main.module';


const routes: Routes = [
  {
    path:'', redirectTo:'landing', pathMatch: 'full',
  },
];

@NgModule({
  imports: [
    MainModule,
    RouterModule.forRoot(routes, {enableTracing: false})],
  exports: [RouterModule],
})
export class AppRoutingModule { }
