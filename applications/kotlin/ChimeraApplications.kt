package chimera.applications

data class ApplicationDescriptor(val id:String,val category:String,val upstream:String,val spdx:String,val platforms:List<String>,val languages:List<String>,val integration:String,val sandbox:String)
