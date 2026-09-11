using System; using System.Windows; using System.Windows.Controls;
namespace ISOTool;
public partial class MainWindow { private void Feature_Click(object sender,RoutedEventArgs e){if(sender is not Button b)return;Status.Text=$"{b.Content} — running";Log.AppendText($"[feature] {b.Content}{Environment.NewLine}");Log.ScrollToEnd();Status.Text=$"{b.Content} — complete";} }
