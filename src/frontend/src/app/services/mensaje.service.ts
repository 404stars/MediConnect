import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class MensajeService {
  private mensaje: string | null = null;

  setMensaje(mensaje: string) {
    this.mensaje = mensaje;
  }

  getMensaje(): string | null {
    const mensaje = this.mensaje;
    this.mensaje = null;
    return mensaje;
  }
}