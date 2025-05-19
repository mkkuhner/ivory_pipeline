# Load code for inference and for allele frequency estimation
# ------------------------------------------------------------
source("likelihoodfunctionsandem.R")
source("calcfreqs.R")
source("~/ElephantProject/Div/colors.R")

# Set run mode 
# ------------------------------------------------------------
runinference=TRUE                  # Set to TRUE the first time the script is run (i.e. results have not yet been obtained), FALSE if is has and all that is needed is plotting)
loaddata=FALSE                     # Set to TRUE if results have already been obtained and stored using this script, but need to be loaded, otherwise set to FALSE
plotres=TRUE			   # Set to TRUE if results should be plotted and FALSE if not
mkxtraplots=TRUE		   # Set to TRUE if xtra plots should be generated and FALSE if not
nullprobgrid   = seq(0,0.5,0.005)  # Define the grid for nullprob used for ML inference (NB no longer assumed to be the same for all sites)
errorprob = 0  	 		   # Fixed errorprob (estimate obtained in infernullalleleprobanderrorrprob.R)  	    	
v=3	    			   # Version number to make sure the correct version of the data is used
datset="all"			   # Set to the dataset that is to be used for ML inference. Choices are: the full dataset ("all") or 1 of the 2 hybrid zones ("Hybzone1" or "Hybzone2")
outpath = "../outfiles/"	   # Path to where the results and plots are saved. NB this folder is assumed to have subfolder called pdfs and a subfolder called data


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



# Do inference of marker specific nullalleleprob (gamma)
# ------------------------------------------------------------
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

# Calc ll for all elephants in a grid of nullprob value but error rate fixed to 0 (estimate obstained in infernullalleleprobanderrorrprob.R) 
overallloglikes = c()
pop1loglikes = c()
pop2loglikes = c()
loglikemats = list()
indspecfreqinfo <- getIndividualSpecificFreqInfo(basicfreqinfo,errorprob=errorprob)
for(m in 1:nmarkers){
   for(nullprob in nullprobgrid){
     nullprobs = matrix(nullprob,nrow=3,ncol=nmarkers)	
     loglikemat = c()
     for(ind in c(purepop1,purepop2)){
        g1s = as.character(dat[(ind*2-1),markeris])
	g2s = as.character(dat[(ind*2)  ,markeris])
     	pseudopop1freqs = indspecfreqinfo$pseudopop1freqslist[[ind]]
     	pseudopop2freqs = indspecfreqinfo$pseudopop2freqslist[[ind]]
	loglike <- c(calcloglikePure(g1s,g2s,pseudopop1freqs,pseudopop2freqs,nullprobs,markers=c(m)),
		     calcloglikePure(g1s,g2s,pseudopop2freqs,pseudopop1freqs,nullprobs[c(2,1,3),],markers=c(m)))
	             if(is.na(loglike[1])){print(i)}
	loglikemat <- rbind(loglikemat,loglike)
     }
     colnames(loglikemat)=c("PurePop1","PurePop2")
     rownames(loglikemat)=c(purepop1,purepop2)
     loglikemats[[paste(nullprob,m,sep="_")]] = loglikemat

     # Calc like for pure elephants
     overallloglike = sum(loglikemat[1:npurepop1,"PurePop1"])+sum(loglikemat[(npurepop1+1):(npurepop1+npurepop2),"PurePop2"])
     overallloglikes = c(overallloglikes,overallloglike)
     pop1loglikes = c(pop1loglikes,sum(loglikemat[1:npurepop1,"PurePop1"]))
     pop2loglikes = c(pop2loglikes,sum(loglikemat[(npurepop1+1):(npurepop1+npurepop2),"PurePop2"]))
     cat("\r",c(m,nullprob,errorprob,overallloglike))
     }
   }

   # Store results
   save(loglikemats,file=paste(outpath,"/data/locuspecloglikemats_",datname,".Rdat",sep=""))
   save(overallloglikes,file=paste(outpath,"/data/locusspecoverallloglikes_",datname,".Rdat",sep=""))
   save(pop1loglikes,file=paste(outpath,"/data/locusspecpop1loglikes_",datname,".Rdat",sep=""))
   save(pop2loglikes,file=paste(outpath,"/data/locusspecpop2loglikes_",datname,".Rdat",sep=""))
}else{
 if(loaddata){
   load(file=paste(outpath,"/data/locuspecloglikemats_",datname,".Rdat",sep=""))
   load(file=paste(outpath,"/data/locusspecoverallloglikes_",datname,".Rdat",sep=""))
   load(file=paste(outpath,"/data/locusspecpop1loglikes_",datname,".Rdat",sep=""))
   load(file=paste(outpath,"/data/locusspecpop2loglikes_",datname,".Rdat",sep=""))
 }
}


# Print ML gammas and store them 
titles = c("purepop1","purepop2","allpure")
MLgammaslist = list()
loglikesmats = list()
loglikes = list()
loglikes[[1]]=pop1loglikes
loglikes[[2]]=pop2loglikes
loglikes[[3]]=overallloglikes

for(i in 1:3){
llsmat = matrix(loglikes[[i]],nrow=length(nullprobgrid),byrow=F)
rownames(llsmat) = paste("Gamma",nullprobgrid,sep="")
colnames(llsmat) = paste("Marker",1:nmarkers,sep="")
loglikesmats[[i]] = llsmat
print(paste("Marker specific ML for gammas for",titles[i])) 
print(nullprobgrid[apply(llsmat,2,which.max)])
print("And the range is:")
print(range(nullprobgrid[apply(llsmat,2,which.max)]))
MLgammas = matrix(nullprobgrid[apply(llsmat,2,which.max)],nrow=1)
colnames(MLgammas) = paste("Marker",1:nmarkers,sep="")
MLgammaslist[[titles[i]]]=MLgammas
}
save(MLgammaslist,file=paste(outpath,"/data/locusspecMLgammas_",datname,".Rdat",sep=""))

if(plotres){
mains = c("only pure forest elephants","only pure savanna elephants","all pure elephants")

# - plot results for all markers
for(i in 1:3){
pdf(paste(outpath,"/pdfs/locusspecloglikesofgammma_errorprob0_",titles[i],"_",datname,".pdf",sep=""))
for(m in 1:nmarkers){
  print(plot(nullprobgrid,loglikesmats[[i]][,m],
        main=paste("Parameter estimation using ",mains[i]," (marker ",m,")",sep=""),
        xlab="Gamma values",ylab="loglikelihood",pch=20,cex=0.85))
  abline(h=max(loglikesmats[[i]][,m])-qchisq(0.95,1)/2,col="red",lty=3)
  abline(v=range(nullprobgrid[which(loglikesmats[[i]][,m]>(max(loglikesmats[[i]][,m])-qchisq(0.95,1)/2))])[1],col="red",lty=3)
  abline(v=range(nullprobgrid[which(loglikesmats[[i]][,m]>(max(loglikesmats[[i]][,m])-qchisq(0.95,1)/2))])[2],col="red",lty=3)
  abline(v=nullprobgrid[which.max(loglikesmats[[i]][,m])],col="red",lty=1)
}
graphics.off()

# - plot zoomed in on ML gamma marker
pdf(paste(outpath,"/pdfs/locusspecloglikesofgammma_errorprob0_",titles[i],"_",datname,"_zoomin.pdf",sep=""))
for(m in 1:nmarkers){
  print(plot(nullprobgrid,loglikesmats[[i]][,m],
	main=paste("Parameter estimation using ",mains[i]," (marker ",m,")",sep=""),
     	ylim=c(max(loglikesmats[[i]][,m])-3,max(loglikesmats[[i]][,m])+0.5),
     	xlab="Gamma values",ylab="loglikelihood",pch=20,cex=0.85))
  abline(h=max(loglikesmats[[i]][,m])-qchisq(0.95,1)/2,col="red",lty=3)
  abline(v=range(nullprobgrid[which(loglikesmats[[i]][,m]>(max(loglikesmats[[i]][,m])-qchisq(0.95,1)/2))])[1],col="red",lty=3)
  abline(v=range(nullprobgrid[which(loglikesmats[[i]][,m]>(max(loglikesmats[[i]][,m])-qchisq(0.95,1)/2))])[2],col="red",lty=3)
  abline(v=nullprobgrid[which.max(loglikesmats[[i]][,m])],col="red",lty=1)
}
graphics.off()
}
# - plot forest vs savanna
pdf(paste(outpath,"/pdfs/locusspecloglikesofgammma_errorprob0_forestvssavanna_",datname,".pdf",sep=""))
plot(MLgammaslist[[1]],MLgammaslist[[2]],pch=20,
     xlim=c(0,max(c(MLgammaslist[[1]]+0.05,MLgammaslist[[2]]+0.05))),
     ylim=c(0,max(c(MLgammaslist[[1]]+0.05,MLgammaslist[[2]]+0.05))),
     xlab="ML gammas estimated for forest",
     ylab="ML gammas estimated for savanna",
     main="Marker specific gamma estimates")

plot(1:nmarkers,MLgammaslist[[1]],pch=20,
     ylim=c(0,max(c(MLgammaslist[[1]]+0.15,MLgammaslist[[2]]+0.15))),
     main="Marker specific gamma estimates",
     xlab="Marker number",ylab="ML gamma estimate",
     col=forestgreen)
points(1:nmarkers,MLgammaslist[[2]],pch=23,col=savannaorange)

ints1 = sapply(1:nmarkers,function(m){range(nullprobgrid[which(loglikesmats[[1]][,m]>(max(loglikesmats[[1]][,m])-qchisq(0.95,1)/2))])})
ints2 = sapply(1:nmarkers,function(m){range(nullprobgrid[which(loglikesmats[[2]][,m]>(max(loglikesmats[[2]][,m])-qchisq(0.95,1)/2))])})
segments(1:nmarkers,ints1[1,],1:nmarkers,ints1[2,],col=forestgreen,lty=3)	
segments(1:nmarkers,ints2[1,],1:nmarkers,ints2[2,],col=savannaorange,lty=2)
legend("topright",legend=c("ML estimate forest","ML estimate savanna","ML+-1.92ll interval forest","ML+-1.92ll interval savanna"),
	                   col=c(forestgreen,savannaorange,
				 forestgreen,savannaorange),
			   pch=c(20,23,NA,NA),lty=c(NA,NA,3,2))
graphics.off()

# - print results
for(i in 1:3){
print(c("marker","ML","[","]"))
for(m in 1:nmarkers){
 print(c(m,nullprobgrid[which.max(loglikesmats[[i]][,m])],
	 range(nullprobgrid[which(loglikesmats[[i]][,m]>(max(loglikesmats[[i]][,m])-qchisq(0.95,1)/2))])))
}

}
}

if(mkxtraplots){
  pdf(paste(outpath,"/pdfs/locusspecloglikesofgammma_errorprob0_forestvssavanna_",datname,"_summary.pdf",sep=""))
  plot(1:nmarkers,MLgammaslist[[1]],pch=20,
       ylim=c(0,max(c(MLgammaslist[[1]]+0.15,MLgammaslist[[2]]+0.25))),
       main=expression(paste("Marker specific ML estimates of ",gamma,sep="")),
       xlab="Marker number",ylab=expression(paste("Marker specific ML estimate of ",gamma,sep="")),
       col=forestgreen)
  points(1:nmarkers,MLgammaslist[[2]],pch=20,col=savannaorange)

  ints1 = sapply(1:nmarkers,function(m){range(nullprobgrid[which(loglikesmats[[1]][,m]>(max(loglikesmats[[1]][,m])-qchisq(0.95,1)/2))])})
  ints2 = sapply(1:nmarkers,function(m){range(nullprobgrid[which(loglikesmats[[2]][,m]>(max(loglikesmats[[2]][,m])-qchisq(0.95,1)/2))])})
  segments(1:nmarkers,ints1[1,],1:nmarkers,ints1[2,],col=forestgreen,lty=3)	
  segments(1:nmarkers,ints2[1,],1:nmarkers,ints2[2,],col=savannaorange,lty=2)
  legend("topright",legend=c("ML estimate from forest elephants","ML estimate from savanna elephants","ML+-1.92ll interval (forest)","ML+-1.92ll interval (savanna)"),
         col=c(forestgreen,savannaorange,
           forestgreen,savannaorange),
         pch=c(20,20,NA,NA),lty=c(NA,NA,3,2))
  graphics.off()
}
