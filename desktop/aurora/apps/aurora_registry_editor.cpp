#include "registry_store.hpp"
#include "registry_paths.hpp"
#include <QApplication>
#include <QHBoxLayout>
#include <QHeaderView>
#include <QLabel>
#include <QLineEdit>
#include <QMessageBox>
#include <QPushButton>
#include <QTableWidget>
#include <QVBoxLayout>
#include <QWidget>
#include <cstdlib>
class RegistryEditor final:public QWidget{
 chimera::hive::RegistryStore store_;QTableWidget* table_{};QLineEdit* key_{};QLineEdit* value_{};
 void refresh(){auto rows=store_.entries();table_->setRowCount(int(rows.size()));int i=0;for(auto&e:rows){table_->setItem(i,0,new QTableWidgetItem(QString::fromStdString(e.first)));table_->setItem(i,1,new QTableWidgetItem(QString::fromStdString(e.second)));++i;}}
 void select(){auto a=table_->selectedItems();if(a.size()>=2){key_->setText(a[0]->text());value_->setText(a[1]->text());}}
 void save(){if(key_->text().isEmpty()){QMessageBox::warning(this,"Hive Registry","A key is required.");return;}if(!store_.set(key_->text().toStdString(),value_->text().toStdString())){QMessageBox::critical(this,"Hive Registry",QString::fromStdString(store_.last_error()));return;}refresh();}
 void remove(){if(key_->text().isEmpty())return;if(QMessageBox::question(this,"Delete value","Delete this registry value?")!=QMessageBox::Yes)return;if(!store_.erase(key_->text().toStdString()))QMessageBox::critical(this,"Hive Registry",QString::fromStdString(store_.last_error()));refresh();}
public:
 RegistryEditor():store_(chimera::hive::paths::registry_directory()){
  setWindowTitle("Aurora — Hive Registry Editor");resize(900,620);auto* root=new QVBoxLayout(this);root->addWidget(new QLabel("Hive Registry — transactional settings database"));
  table_=new QTableWidget(0,2,this);table_->setHorizontalHeaderLabels({"Key","Value"});table_->horizontalHeader()->setStretchLastSection(true);root->addWidget(table_);
  auto* row=new QHBoxLayout;key_=new QLineEdit;key_->setPlaceholderText("registry/key");value_=new QLineEdit;value_->setPlaceholderText("value");row->addWidget(key_);row->addWidget(value_);root->addLayout(row);
  auto* actions=new QHBoxLayout;auto* saveBtn=new QPushButton("Save / Modify");auto* delBtn=new QPushButton("Delete");auto* checkpointBtn=new QPushButton("Checkpoint / Recover");actions->addWidget(saveBtn);actions->addWidget(delBtn);actions->addWidget(checkpointBtn);root->addLayout(actions);
  connect(table_,&QTableWidget::itemSelectionChanged,this,[this]{select();});connect(saveBtn,&QPushButton::clicked,this,[this]{save();});connect(delBtn,&QPushButton::clicked,this,[this]{remove();});connect(checkpointBtn,&QPushButton::clicked,this,[this]{if(!store_.compact())QMessageBox::critical(this,"Hive Registry",QString::fromStdString(store_.last_error()));else QMessageBox::information(this,"Hive Registry","Checkpoint completed.");});
  if(!store_.open())QMessageBox::critical(this,"Hive Registry",QString::fromStdString(store_.last_error()));else refresh();
 }
};
int main(int argc,char**argv){QApplication app(argc,argv);RegistryEditor w;w.show();return app.exec();}
