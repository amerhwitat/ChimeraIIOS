package chimera.quantum;

public final class ChimeraQuantum {
  public static final class StateVector {
    public final int qubits; public final double[] re; public final double[] im;
    public StateVector(int qubits) { if (qubits < 1) throw new IllegalArgumentException(); this.qubits=qubits; re=new double[1<<qubits]; im=new double[1<<qubits]; re[0]=1; }
    public double probabilitySum(){ double s=0; for(int i=0;i<re.length;i++) s+=re[i]*re[i]+im[i]*im[i]; return s; }
    public void hadamard(int target){ if(target<0||target>=qubits) throw new IndexOutOfBoundsException(); int bit=1<<target; double k=1/Math.sqrt(2); for(int i=0;i<re.length;i++) if((i&bit)==0){int j=i|bit; double xr=re[i],xi=im[i],yr=re[j],yi=im[j]; re[i]=k*(xr+yr); im[i]=k*(xi+yi); re[j]=k*(xr-yr); im[j]=k*(xi-yi);} }
  }
}
