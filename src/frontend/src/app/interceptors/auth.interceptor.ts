import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, BehaviorSubject } from 'rxjs';
import { catchError, switchMap, filter, take } from 'rxjs/operators';
import { Router } from '@angular/router';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private isRefreshing = false;
  private refreshTokenSubject: BehaviorSubject<any> = new BehaviorSubject<any>(null);
  private sessionExpiredShown = false;

  constructor(private router: Router) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    return next.handle(req).pipe(
      catchError((error: HttpErrorResponse) => {
        const isLoginRequest = req.url.includes('/auth/login') || req.url.includes('/auth/register');
        const isPasswordRecovery = req.url.includes('/recuperar-password') || req.url.includes('/restablecer-password');
        const hasToken = !!localStorage.getItem('auth_token');
        const isTokenError = error.error?.detail?.includes('Token inválido') || 
                           error.error?.detail?.includes('Token expirado') ||
                           error.error?.detail?.includes('sesión expirada');
        
        // Solo manejar token expirado si:
        // 1. NO es una petición de login/registro
        // 2. NO es recuperación de contraseña
        // 3. SÍ hay un token guardado (estaba logueado)
        // 4. Es un error de token explícito O un 403 (forbidden)
        if (!isLoginRequest && 
            !isPasswordRecovery && 
            hasToken &&
            (error.status === 401 || error.status === 403) &&
            (isTokenError || error.status === 403)) {
          
          console.warn('Token expirado o inválido. Cerrando sesión...');
          this.handleTokenExpired();
          return throwError(() => error);
        }
        
        // Para cualquier otro error (incluido login fallido), solo propagarlo
        return throwError(() => error);
      })
    );
  }

  private handleTokenExpired(): void {
    if (this.sessionExpiredShown) {
      return;
    }
    
    this.sessionExpiredShown = true;
    
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    localStorage.removeItem('active_role');
    localStorage.removeItem('user_roles');
    localStorage.removeItem('additional_info');
    
    alert('Su sesión ha expirado. Por favor, inicie sesión nuevamente.');
    
    this.router.navigate(['/login']).then(() => {
      setTimeout(() => {
        this.sessionExpiredShown = false;
      }, 1000);
    });
  }
}
