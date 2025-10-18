import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Navbar } from '../shared/navbar/navbar';
import { AuthService } from '../services/auth.service';
import { AdminService, CitaAdmin } from '../services/admin.service';

@Component({
  selector: 'app-gestion-citas',
  templateUrl: './gestion-citas.html',
  styleUrls: ['./gestion-citas.css'],
  standalone: true,
  imports: [CommonModule, FormsModule, Navbar]
})
export class GestionCitas implements OnInit {
  citas: CitaAdmin[] = [];
  citasFiltradas: CitaAdmin[] = [];
  especialidades: {nombre: string}[] = [];
  isLoading: boolean = false;
  message: string = '';
  
  mostrarEstadisticas: boolean = false;
  estadisticas: any = null;
  
  mostrarModalConfirmacion: boolean = false;
  accionModal: 'atendida' | 'no-asistio' | null = null;
  citaSeleccionada: number | null = null;
  
  filtroEstado: string = '';
  filtroFechaDesde: string = '';
  filtroFechaHasta: string = '';
  filtroProfesional: string = '';
  filtroEspecialidad: string = '';
  filtroRutPaciente: string = '';
  
  
  currentPage: number = 1;
  pageSize: number = 20;
  totalCitas: number = 0;
  
  
  estados = [
    { valor: '', texto: 'Todos los estados' },
    { valor: 'AGENDADA', texto: 'Agendadas' },
    { valor: 'CONFIRMADA', texto: 'Confirmadas' },
    { valor: 'EN_ATENCION', texto: 'En Atención' },
    { valor: 'ATENDIDA', texto: 'Atendidas' },
    { valor: 'CANCELADA', texto: 'Canceladas' },
    { valor: 'NO_ASISTIO', texto: 'No Asistió' }
  ];

  constructor(
    private adminService: AdminService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit() {
    window.scrollTo(0, 0);
    
    if (!this.authService.hasRole('Administrador')) {
      this.router.navigate(['/']);
      return;
    }

    this.cargarTodasLasCitas();
    this.cargarEspecialidades();
  }

  cargarEspecialidades() {
    this.adminService.getEspecialidades().subscribe({
      next: (especialidades) => {
        this.especialidades = especialidades;
      },
      error: (error) => {
        console.error('Error cargando especialidades:', error);
        this.message = '[ERROR] Error al cargar especialidades';
      }
    });
  }

  cargarTodasLasCitas() {
    this.isLoading = true;
    this.message = '';

    const skip = (this.currentPage - 1) * this.pageSize;
    const params = {
      skip: skip,
      limit: this.pageSize,
      ...(this.filtroEstado && { estado: this.filtroEstado }),
      ...(this.filtroFechaDesde && { fecha_desde: this.filtroFechaDesde }),
      ...(this.filtroFechaHasta && { fecha_hasta: this.filtroFechaHasta }),
      ...(this.filtroRutPaciente && { paciente_rut: this.filtroRutPaciente })
    };

    
    this.adminService.getTodasLasCitas(params).subscribe({
      next: (response) => {
        this.citas = response;
        this.aplicarFiltrosLocales();
        this.isLoading = false;
        
        if (this.citas.length === 0) {
          this.message = '[WARNING] No se encontraron citas con los filtros aplicados.';
        }
      },
      error: (error) => {
        console.error('Error al cargar las citas:', error);
        this.message = '[ERROR] Error al cargar las citas. Intente nuevamente.';
        this.isLoading = false;
      }
    });
  }

  aplicarFiltrosLocales() {
    this.citasFiltradas = this.citas.filter(cita => {
      
      if (this.filtroProfesional) {
        const nombreCompleto = `${cita.profesional.nombres} ${cita.profesional.apellidos}`.toLowerCase();
        if (!nombreCompleto.includes(this.filtroProfesional.toLowerCase())) {
          return false;
        }
      }

      
      if (this.filtroEspecialidad) {
        if (!cita.profesional.especialidad.nombre.toLowerCase().includes(this.filtroEspecialidad.toLowerCase())) {
          return false;
        }
      }

      return true;
    });

    this.totalCitas = this.citasFiltradas.length;
  }

  onFiltroChange() {
    this.currentPage = 1;
    this.cargarTodasLasCitas();
  }

  onFiltroLocalChange() {
    this.aplicarFiltrosLocales();
  }

  limpiarFiltros() {
    this.filtroEstado = '';
    this.filtroFechaDesde = '';
    this.filtroFechaHasta = '';
    this.filtroProfesional = '';
    this.filtroEspecialidad = '';
    this.filtroRutPaciente = '';
    this.currentPage = 1;
    this.cargarTodasLasCitas();
  }

  aplicarFiltroRapido(estado: string) {
    this.filtroEstado = estado;
    this.currentPage = 1;
    this.cargarTodasLasCitas();
  }

  cambiarPagina(pagina: number) {
    if (pagina >= 1 && pagina <= this.getTotalPages()) {
      this.currentPage = pagina;
      this.cargarTodasLasCitas();
    }
  }

  getTotalPages(): number {
    return Math.ceil(this.totalCitas / this.pageSize);
  }

  getEstadoBadgeClass(estado: string): string {
    const clases: { [key: string]: string } = {
      'AGENDADA': 'bg-primary',
      'CONFIRMADA': 'bg-success',
      'EN_ATENCION': 'bg-warning text-dark',
      'ATENDIDA': 'bg-info text-dark',
      'CANCELADA': 'bg-danger',
      'NO_ASISTIO': 'bg-secondary'
    };
    return clases[estado] || 'bg-light text-dark';
  }

  formatearFecha(fecha: string): string {
    const [year, month, day] = fecha.split('-').map(Number);
    const date = new Date(year, month - 1, day);
    return date.toLocaleDateString('es-CL');
  }

  formatearHora(hora: string): string {
    return hora.substring(0, 5); 
  }

  contarPorEstado(estado: string): number {
    return this.citasFiltradas.filter(cita => cita.estado === estado).length;
  }

  exportarCSV() {
    this.isLoading = true;
    const filtros = {
      estado: this.filtroEstado,
      fecha_desde: this.filtroFechaDesde,
      fecha_hasta: this.filtroFechaHasta,
      profesional: this.filtroProfesional,
      especialidad: this.filtroEspecialidad,
      rut_paciente: this.filtroRutPaciente
    };

    this.adminService.exportarReporteCitas(filtros).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        
        const fechaActual = new Date().toISOString().split('T')[0];
        const nombreArchivo = `reporte_citas_${fechaActual}.csv`;
        link.download = nombreArchivo;
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        this.message = '[SUCCESS] Reporte exportado exitosamente';
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error exportando reporte:', error);
        this.message = '[ERROR] Error al exportar el reporte';
        this.isLoading = false;
      }
    });
  }

  exportarPacientesAtendidos() {
    this.isLoading = true;
    this.message = '';

    const filtros = {
      fecha_desde: this.filtroFechaDesde,
      fecha_hasta: this.filtroFechaHasta,
      especialidad: this.filtroEspecialidad,
      profesional: this.filtroProfesional
    };

    this.adminService.exportarPacientesAtendidos(filtros).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        
        const fechaActual = new Date().toISOString().split('T')[0];
        const nombreArchivo = `pacientes_atendidos_${fechaActual}.csv`;
        link.download = nombreArchivo;
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        this.message = 'Reporte de pacientes atendidos exportado exitosamente';
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error exportando reporte de pacientes atendidos:', error);
        this.message = 'Error al exportar el reporte de pacientes atendidos';
        this.isLoading = false;
      }
    });
  }

  verEstadisticas() {
    this.mostrarEstadisticas = !this.mostrarEstadisticas;
    
    if (this.mostrarEstadisticas && !this.estadisticas) {
      this.cargarEstadisticas();
    }
  }

  cargarEstadisticas() {
    this.isLoading = true;
    this.message = '';

    const filtros = {
      fecha_desde: this.filtroFechaDesde,
      fecha_hasta: this.filtroFechaHasta,
      especialidad: this.filtroEspecialidad
    };

    this.adminService.getEstadisticasUtilizacion(filtros).subscribe({
      next: (stats) => {
        this.estadisticas = stats;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error obteniendo estadísticas:', error);
        this.message = '[ERROR] Error al obtener estadísticas';
        this.isLoading = false;
        this.mostrarEstadisticas = false;
      }
    });
  }

  abrirModalConfirmacion(citaId: number, accion: 'atendida' | 'no-asistio') {
    this.citaSeleccionada = citaId;
    this.accionModal = accion;
    this.mostrarModalConfirmacion = true;
  }

  cerrarModalConfirmacion() {
    this.mostrarModalConfirmacion = false;
    this.citaSeleccionada = null;
    this.accionModal = null;
  }

  confirmarAccion() {
    if (!this.citaSeleccionada || !this.accionModal) {
      return;
    }

    if (this.accionModal === 'atendida') {
      this.marcarComoAtendida(this.citaSeleccionada);
    } else if (this.accionModal === 'no-asistio') {
      this.marcarComoNoAsistio(this.citaSeleccionada);
    }

    this.cerrarModalConfirmacion();
  }

  marcarComoAtendida(citaId: number) {
    this.isLoading = true;
    this.adminService.marcarCitaAtendida(citaId).subscribe({
      next: () => {
        this.message = '[SUCCESS] Cita marcada como atendida exitosamente';
        this.cargarTodasLasCitas();
      },
      error: (error) => {
        console.error('Error marcando cita como atendida:', error);
        this.message = 'Error al marcar la cita como atendida';
        this.isLoading = false;
      }
    });
  }

  marcarComoNoAsistio(citaId: number) {
    this.isLoading = true;
    this.adminService.marcarCitaNoAsistio(citaId).subscribe({
      next: () => {
        this.message = 'Cita marcada como NO ASISTIÓ';
        this.cargarTodasLasCitas();
      },
      error: (error) => {
        console.error('Error marcando cita como no asistió:', error);
        this.message = 'Error al marcar la cita';
        this.isLoading = false;
      }
    });
  }

  getMensajeModal(): string {
    if (this.accionModal === 'atendida') {
      return '¿Confirmar que el paciente fue atendido?';
    } else if (this.accionModal === 'no-asistio') {
      return '¿Confirmar que el paciente NO asistió a la cita?';
    }
    return '';
  }
}
