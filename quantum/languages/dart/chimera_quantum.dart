import 'dart:math' as math;

class ChimeraStateVector {
  final int qubits; final List<double> re; final List<double> im;
  ChimeraStateVector(this.qubits) : re=List.filled(1<<qubits,0.0), im=List.filled(1<<qubits,0.0) { if(qubits<1) throw ArgumentError('qubits'); re[0]=1.0; }
  double probabilitySum()=>List.generate(re.length,(i)=>re[i]*re[i]+im[i]*im[i]).reduce((a,b)=>a+b);
  void hadamard(int target){ if(target<0||target>=qubits) throw RangeError('target'); final bit=1<<target,k=1/math.sqrt(2); for(var i=0;i<re.length;i++) if((i&bit)==0){final j=i|bit,xr=re[i],xi=im[i],yr=re[j],yi=im[j]; re[i]=k*(xr+yr); im[i]=k*(xi+yi); re[j]=k*(xr-yr); im[j]=k*(xi-yi);} }
}

class ChimeraQuantum { static List<double> bellProbabilities()=>[0.5,0.0,0.0,0.5]; }
