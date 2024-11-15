import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { HomeComponent } from './home/home.component';
import { ObservationComponent } from './observation/observation.component';
import { PulsarComponent } from './pulsar/pulsar.component';
import { CalculatorComponent } from './calculator/calculator.component';
import { ArchiveComponent } from './archive/archive.component';
import { ProposalComponent } from './proposal/proposal.component';


export const routes: Routes = [
  { path: '', component: HomeComponent},
  { path: 'observation', component: ObservationComponent},
  { path: 'pulsar', component: PulsarComponent },
  { path: 'calculator', component: CalculatorComponent},
  { path: 'archive', component: ArchiveComponent},
  { path: 'proposal', component: ProposalComponent}
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }

