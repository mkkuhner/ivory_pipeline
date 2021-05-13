# Load code for inference and for allele frequency estimation
# ------------------------------------------------------------
source("likelihoodfunctionsandem.R")
source("calcfreqs.R")

# Set run mode
# ------------------------------------------------------------

runinference=TRUE                   # Set to TRUE the first time the script is run (i.e. results have not yet been obtained), FALSE if is has and all that is needed is plotting)
loaddata=FALSE                      # Set to TRUE if results have already been obtained and stored using this script, but need to be loaded, otherwise set to FALSE
plotres=TRUE                        # Set to TRUE if results should be plotted and FALSE if not
nullprobgrid   = seq(0,0.5,0.005)   # Define the grid for nullprob used for ML inference (NB assumed to be the same for all sites)  
errorprobgrid  = seq(0,0.15,0.005)  # Define the grid for errorprob used for ML inference (NB assumed to be the same for all sites) 
v=3	       	 		    # Version number to make sure the correct version of the data is used 
datset = "all"                      # Set to the dataset that is to be used for ML inference. Choices are: the full dataset ("all") or 1 of the 2 hybrid zones ("Hybzone1" or "Hybzone2")
outpath = "../outfiles/"        # Path to where the results and plots are saved. NB this folder is assumed to have subfolder called pdfs and a subfolder called data
   

# Specify where to find the data to analyses and read in data to analyse 
# -------------------------------------------------------------------------
# (this data consists of the genotype data 'dat', the results from STRUCTURE 'structres' and number of markers 'nmarkers' need to be specified)
# NB note that the paths for where to find this will also need to be adjusted in not run in Ida's original folders

if(datset=="all"){
  datname=paste("All-Structurewithloc_V",v,sep="")
  structinputfile = paste("~/ElephantProject/Data/datasets/",datname,".txt",sep="")
  dat <- read.table(structinputfile,as.is=T)
  structresfile = paste("~/ElephantProject/StructureAnalysis/plot/input/",datname,"_inferpopspecalpha_K2_run1_f.indsq",sep="")
  structres <- read.table(structresfile,as.is=T)[,c(2,1)]
  nmarkers = 16
}

if(datset=="Hybzone1"){
  datname=paste("All-Structurewithloc_V",v,"b_Hybzone1",sep="")
  structinputfile = paste("~/ElephantProject/Data/datasets/",datname,".txt",sep="")
  dat <- read.table(structinputfile,as.is=T)
  structresfile = paste("~/ElephantProject/StructureAnalysis/plot/input/",datname,"_inferpopspecalpha_K2_run1_f.indsq",sep="") 
  structres <- read.table(structresfile,as.is=T)[,c(2,1)]
  nmarkers = 16
}

if(datset=="Hybzone2"){
  datname=paste("All-Structurewithloc_V",v,"b_Hybzone2",sep="")
  structinputfile = paste("~/ElephantProject/Data/datasets/",datname,".txt",sep="")
  dat <- read.table(structinputfile,as.is=T)
  structresfile = paste("~/ElephantProject/StructureAnalysis/plot/input/",datname,"_inferpopspecalpha_K2_run1_f.indsq",sep="") 
  structres <- read.table(structresfile,as.is=T)[,c(2,1)]
  nmarkers = 16
}


# Do ML inference of error rates assuming null prob (gamma) is the same for all sites
# -------------------------------------------------------------------------------------
if(runinference){

# Set basic info
lastmarkeri = dim(dat)[2]
firstmarkeri = lastmarkeri-nmarkers+1
markeris = firstmarkeri:lastmarkeri
ninds = dim(dat)[1]/2

# Estimate allele frequencies
basicfreqinfo <- getBasicFreqInfo(dat,structres,structthres=0.95)
purepop1 <- basicfreqinfo$purepop1
purepop2 <- basicfreqinfo$purepop2
npurepop1 <- length(purepop1)
npurepop2 <- length(purepop2)

# Calc ll for all elephants in a grid of nullprob value, error prob value combinations
overallloglikes = c()
pop1loglikes = c()
pop2loglikes = c()
loglikemats = list()
for(nullprob in nullprobgrid){
  nullprobs = matrix(nullprob,ncol=nmarkers,nrow=3)
  for(errorprob in errorprobgrid){ 
     indspecfreqinfo <- getIndividualSpecificFreqInfo(basicfreqinfo,errorprob=errorprob)
     loglikemat = c()
     for(ind in c(purepop1,purepop2)){
        g1s = as.character(dat[(ind*2-1),markeris])
	g2s = as.character(dat[(ind*2)  ,markeris])
     	pseudopop1freqs = indspecfreqinfo$pseudopop1freqslist[[ind]]
     	pseudopop2freqs = indspecfreqinfo$pseudopop2freqslist[[ind]]
	loglike <- c(calcloglikePure(g1s,g2s,pseudopop1freqs,pseudopop2freqs,nullprobs),
		     calcloglikePure(g1s,g2s,pseudopop2freqs,pseudopop1freqs,nullprobs))
	             if(is.na(loglike[1])){print(i)}
	loglikemat <- rbind(loglikemat,loglike)
     }
     colnames(loglikemat)=c("PurePop1","PurePop2")
     rownames(loglikemat)=c(purepop1,purepop2)
     loglikemats[[paste(nullprob,errorprob,sep="")]] = loglikemat

     # Calc like for pure elephants
     overallloglike = sum(loglikemat[1:npurepop1,"PurePop1"])+sum(loglikemat[(npurepop1+1):(npurepop1+npurepop2),"PurePop2"])
     overallloglikes = c(overallloglikes,overallloglike)
     pop1loglikes = c(pop1loglikes,sum(loglikemat[1:npurepop1,"PurePop1"]))
     pop2loglikes = c(pop2loglikes,sum(loglikemat[(npurepop1+1):(npurepop1+npurepop2),"PurePop2"]))
     cat("\r",c(nullprob,errorprob,overallloglike))
    }
  }
  # Store results
  save(loglikemats,file=paste(outpath,"/data/loglikemats_",datname,".Rdat",sep=""))
  save(overallloglikes,file=paste(outpath,"/data/overallloglikes_",datname,".Rdat",sep=""))
  save(pop1loglikes,file=paste(outpath,"/data/pop1loglikes_",datname,".Rdat",sep=""))
  save(pop2loglikes,file=paste(outpath,"/data/pop2loglikes_",datname,".Rdat",sep=""))
}else{
 if(loaddata){
  load(file=paste(outpath,"/data/loglikemats_",datname,".Rdat",sep=""))
  load(file=paste(outpath,"/data/overallloglikes_",datname,".Rdat",sep=""))
  load(file=paste(outpath,"/data/pop1loglikes_",datname,".Rdat",sep=""))
  load(file=paste(outpath,"/data/pop2loglikes_",datname,".Rdat",sep=""))
 }
}


if(plotres){

## Extract the values with highest ll
overallloglikesmat = matrix(overallloglikes,nrow=length(nullprobgrid),byrow=T)
rownames(overallloglikesmat) = paste("Gamma",nullprobgrid,sep="")
colnames(overallloglikesmat) = paste("Error",errorprobgrid,sep="")
print(which(overallloglikesmat==max(overallloglikesmat),arr.ind=T))
# All
#          row col
#Gamma0.08  17   1

pop1loglikesmat = matrix(pop1loglikes,nrow=length(nullprobgrid),byrow=T)
rownames(pop1loglikesmat) = paste("Gamma",nullprobgrid,sep="")
colnames(pop1loglikesmat) = paste("Error",errorprobgrid,sep="")
print(which(pop1loglikesmat==max(pop1loglikesmat),arr.ind=T))
# All
#          row col
#Gamma0.15  31   1

pop2loglikesmat = matrix(pop2loglikes,nrow=length(nullprobgrid),byrow=T)
rownames(pop2loglikesmat) = paste("Gamma",nullprobgrid,sep="")
colnames(pop2loglikesmat) = paste("Error",errorprobgrid,sep="")
print(which(pop2loglikesmat==max(pop2loglikesmat),arr.ind=T))
# All
#           row col
#Gamma0.045  10   1

## So for all three (overall, pop1 and pop2) the highest likelihood is in the first column so when the error rate is 0. 
## This number was therefore used in the paper. 
## Below plots and numbers illustrate all results with error rate 0 (but assuming all sites have the same gamma 
## so the below is not used directly in the paper)
 
print(range(nullprobgrid[which(overallloglikesmat[,"Error0"]>(max(overallloglikesmat[,"Error0"])-qchisq(0.95,1)/2))]))
# All
#[1] 0.075 0.085
print(range(nullprobgrid[which(pop1loglikesmat[,"Error0"]>(max(pop1loglikesmat[,"Error0"])-qchisq(0.95,1)/2))]))
# Pop1
#[1] 0.140 0.165
print(range(nullprobgrid[which(pop2loglikesmat[,"Error0"]>(max(pop2loglikesmat[,"Error0"])-qchisq(0.95,1)/2))]))
# Pop2
#[1] 0.04 0.055


mains = c("only forest elephants","only savanna elephants","all pure elephants")
res = list()
res[[1]] = pop1loglikesmat
res[[2]] = pop2loglikesmat
res[[3]] = overallloglikesmat

pdf(paste(outpath,"/pdfs/loglikesofgammma_errorprob0_",datname,".pdf",sep=""))
for(resi in 1:3){
print(plot(nullprobgrid,res[[resi]][,"Error0"],
           main=paste("Parameter estimation using",mains[resi]),
           xlab="Gamma values",ylab="loglikelihood",pch=20,cex=0.85))
abline(h=max(res[[resi]][,"Error0"])-qchisq(0.95,1)/2,col="red")
abline(v=range(nullprobgrid[which(res[[resi]][,"Error0"]>(max(res[[resi]][,"Error0"])-qchisq(0.95,1)/2))])[1],col="red",lty=3)
abline(v=range(nullprobgrid[which(res[[resi]][,"Error0"]>(max(res[[resi]][,"Error0"])-qchisq(0.95,1)/2))])[2],col="red",lty=3)
print(plot(nullprobgrid,res[[resi]][,"Error0"],
           main=paste("Parameter estimation using",mains[resi]),
     	   ylim=c(max(res[[resi]][,"Error0"])-3,max(res[[resi]][,"Error0"])+0.5),
     	   xlab="Gamma values",ylab="loglikelihood",pch=20,cex=0.85))
abline(h=max(res[[resi]][,"Error0"])-qchisq(0.95,1)/2,col="red")
abline(v=range(nullprobgrid[which(res[[resi]][,"Error0"]>(max(res[[resi]][,"Error0"])-qchisq(0.95,1)/2))])[1],col="red",lty=3)
abline(v=range(nullprobgrid[which(res[[resi]][,"Error0"]>(max(res[[resi]][,"Error0"])-qchisq(0.95,1)/2))])[2],col="red",lty=3)
}
graphics.off()


pdf(paste(outpath,"/pdfs/loglikesoferrorprob_gammafixedtoML_",datname,".pdf",sep=""))
for(resi in 1:3){
MLgamma = nullprobgrid[which.max(res[[resi]][,"Error0"])]
print(plot(errorprobgrid,pop1loglikesmat[paste("Gamma",MLgamma,sep=""),],pch=20,xlab="Error rate",ylab="loglikelihood",
      main=paste("Estimation of error rates using ",mains[resi]," (gamma ",MLgamma,")",sep=""),cex=0.8,cex.main=.98))
}
graphics.off()

}



