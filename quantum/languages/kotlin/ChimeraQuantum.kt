package chimera.quantum

object ChimeraQuantum {
  class StateVector(val qubits: Int) {
    val re = DoubleArray(1 shl qubits)
    val im = DoubleArray(1 shl qubits)
    init { require(qubits > 0); re[0] = 1.0 }
    fun probabilitySum() = re.indices.sumOf { re[it]*re[it] + im[it]*im[it] }
    fun hadamard(target: Int) {
      require(target in 0 until qubits); val bit=1 shl target; val k=1.0/kotlin.math.sqrt(2.0)
      for(i in re.indices) if(i and bit == 0){ val j=i or bit; val xr=re[i]; val xi=im[i]; val yr=re[j]; val yi=im[j]; re[i]=k*(xr+yr); im[i]=k*(xi+yi); re[j]=k*(xr-yr); im[j]=k*(xi-yi) }
    }
  }
}
