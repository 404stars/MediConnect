import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { NotificationService } from '../services/notification.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {
  constructor(private authService: AuthService, private router: Router) {}

  canActivate(): boolean {
    if (this.authService.isLoggedIn()) {
      return true;
    } else {
      this.router.navigate(['/login']);
      return false;
    }
  }
}

@Injectable({
  providedIn: 'root'
})
export class ActiveRoleGuard implements CanActivate {
  constructor(
    private authService: AuthService, 
    private router: Router,
    private notificationService: NotificationService
  ) {}

  canActivate(): boolean {
    const isLoggedIn = this.authService.isLoggedIn();
    const activeRole = this.authService.getActiveRole();
    const user = this.authService.getCurrentUser();
    
    if (!isLoggedIn) {
      this.router.navigate(['/login']);
      return false;
    }
    
    if (user && user.roles && user.roles.length > 0 && !activeRole) {
      this.notificationService.showWarning(
        'Selecciona un Rol',
        'Debes seleccionar un rol antes de acceder a esta sección. Por favor, selecciona el rol con el que deseas continuar.'
      );
      setTimeout(() => {
        this.router.navigate(['/selector-rol']);
      }, 100);
      return false;
    }
    
    if (activeRole) {
      return true;
    }
    
    this.notificationService.showError(
      'Sin Roles Asignados',
      'No tienes roles asignados en el sistema. Por favor, contacta con el administrador para obtener acceso.'
    );
    setTimeout(() => {
      this.router.navigate(['/login']);
    }, 100);
    return false;
  }
}

@Injectable({
  providedIn: 'root'
})
export class RoleGuard implements CanActivate {
  constructor(private authService: AuthService, private router: Router) {}

  canActivate(): boolean {
    console.log('RoleGuard: Verificando acceso a administración');
    console.log('RoleGuard: Usuario logueado:', this.authService.isLoggedIn());
    console.log('RoleGuard: Roles del usuario:', this.authService.getCurrentUserRoles());
    
    const isLoggedIn = this.authService.isLoggedIn();
    const hasAdminRole = this.authService.hasRole('ADMINISTRADOR_SISTEMA') || this.authService.hasRole('Administrador');
    
    console.log('RoleGuard: Tiene rol admin:', hasAdminRole);
    
    if (isLoggedIn && hasAdminRole) {
      console.log('RoleGuard: Acceso permitido');
      return true;
    } else {
      console.log('RoleGuard: Acceso denegado, redirigiendo a /');
      this.router.navigate(['/']);
      return false;
    }
  }
}
