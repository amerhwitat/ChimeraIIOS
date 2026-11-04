subroutine chimera_sdk_fortran_smoke(value) bind(C, name="chimera_sdk_fortran_smoke")
  use iso_c_binding
  integer(c_int), intent(out) :: value
  value = 1
end subroutine chimera_sdk_fortran_smoke
