import Foundation

public struct ChimeraStateVector {
    public let qubits: Int
    public var re: [Double]
    public var im: [Double]
    public init(qubits: Int) { precondition(qubits > 0); self.qubits=qubits; re=Array(repeating:0,count:1<<qubits); im=Array(repeating:0,count:1<<qubits); re[0]=1 }
    public func probabilitySum() -> Double { zip(re,im).reduce(0){$0 + $1.0*$1.0 + $1.1*$1.1} }
    public mutating func hadamard(_ target: Int) { precondition(target >= 0 && target < qubits); let bit=1<<target; let k=1.0/sqrt(2); for i in 0..<re.count where i & bit == 0 { let j=i|bit; let xr=re[i],xi=im[i],yr=re[j],yi=im[j]; re[i]=k*(xr+yr); im[i]=k*(xi+yi); re[j]=k*(xr-yr); im[j]=k*(xi-yi) } }
}

public enum ChimeraQuantum { public static func bellProbabilities()->[Double]{[0.5,0.0,0.0,0.5]} }
