namespace Chimera.Quantum {
  public static class ChimeraQuantum {
    public sealed class StateVector {
      public int Qubits { get; } public double[] Re { get; } public double[] Im { get; }
      public StateVector(int qubits) { if(qubits<1) throw new System.ArgumentOutOfRangeException(nameof(qubits)); Qubits=qubits; Re=new double[1<<qubits]; Im=new double[1<<qubits]; Re[0]=1; }
      public double ProbabilitySum(){ double s=0; for(int i=0;i<Re.Length;i++) s+=Re[i]*Re[i]+Im[i]*Im[i]; return s; }
      public void Hadamard(int target){ if(target<0||target>=Qubits) throw new System.ArgumentOutOfRangeException(nameof(target)); int bit=1<<target; double k=1/System.Math.Sqrt(2); for(int i=0;i<Re.Length;i++) if((i&bit)==0){int j=i|bit; double xr=Re[i],xi=Im[i],yr=Re[j],yi=Im[j]; Re[i]=k*(xr+yr); Im[i]=k*(xi+yi); Re[j]=k*(xr-yr); Im[j]=k*(xi-yi);} }
    }
  }
}
