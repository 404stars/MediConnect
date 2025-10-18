import { Component } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { PasswordService } from './services/password.service';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Navbar } from './shared/navbar/navbar';

@Component({
  selector: 'app-restablecer-password',
  standalone: true,
  imports: [CommonModule, FormsModule, Navbar],
  templateUrl: './restablecer-password.component.html',
  
})
export class RestablecerPasswordComponent {
  nuevaPassword: string = '';
  mensaje: string = '';
  loading = false;
  token: string = '';
  showPassword: boolean = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private passwordService: PasswordService
  ) {
    this.route.queryParams.subscribe(params => {
      this.token = params['token'] || '';
    });
  }

  restablecerPassword() {
    this.loading = true;
    this.passwordService.restablecerPassword(this.token, this.nuevaPassword).subscribe({
      next: () => {
        this.mensaje = '[SUCCESS] Contraseña restablecida exitosamente. Puedes iniciar sesión.';
        this.loading = false;
        setTimeout(() => this.router.navigate(['/login']), 2000);
      },
      error: () => {
        this.mensaje = '[ERROR] Error al restablecer la contraseña. El enlace puede haber expirado.';
        this.loading = false;
      }
    });
  }
}
