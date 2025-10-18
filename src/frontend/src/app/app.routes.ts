import { Routes } from '@angular/router';
import { Login } from './login/login';
import { Registro } from './registro/registro';
import { Perfil } from './perfil/perfil';
import { PedirHora } from './pedir-hora/pedir-hora';
import { MisHoras } from './mis-horas/mis-horas';
import { AgendaMedica } from './agenda-medica/agenda-medica';
import { Administracion } from './administracion/administracion';
import { GestionHorariosComponent } from './gestion-horarios/gestion-horarios.component';
import { GestionCitas } from './gestion-citas/gestion-citas';
import { SolicitarRecuperacionComponent } from './solicitar-recuperacion.component';
import { RestablecerPasswordComponent } from './restablecer-password.component';
import { SelectorRolComponent } from './selector-rol/selector-rol.component';
import { AuthGuard, RoleGuard, ActiveRoleGuard } from './services/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: 'login', component: Login },
  { path: 'registro', component: Registro },
  { path: 'selector-rol', component: SelectorRolComponent, canActivate: [AuthGuard] },
  { path: 'perfil', component: Perfil, canActivate: [ActiveRoleGuard] },
  { path: 'pedir-hora', component: PedirHora, canActivate: [ActiveRoleGuard] },
  { path: 'mis-horas', component: MisHoras, canActivate: [ActiveRoleGuard] },
  { path: 'agenda-medica', component: AgendaMedica, canActivate: [ActiveRoleGuard] },
  { path: 'administracion', component: Administracion, canActivate: [ActiveRoleGuard] },
  { path: 'gestion-horarios', component: GestionHorariosComponent, canActivate: [ActiveRoleGuard] },
  { path: 'gestion-citas', component: GestionCitas, canActivate: [ActiveRoleGuard] },
  { path: 'recuperar-password', component: SolicitarRecuperacionComponent },
  { path: 'restablecer-password', component: RestablecerPasswordComponent }
];
