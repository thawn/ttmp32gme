
package TTMp32Gme::Build::Mac;

use strict;
use warnings;

use File::Copy;
use File::Find;
use File::Path qw(make_path);
use Path::Class;
require Exporter;
our @ISA = qw(Exporter);
our @EXPORT = qw(loadFile getLibraryPath loadTemplates loadAssets checkConfigFile openBrowser);

print "Mac include\n";

sub loadFile {
 	my $path = $_[0];
 	my $content = PAR::read_file($path);
 	return $content;
}

sub getLibraryPath {
	my $library = (dir($ENV{'HOME'} , 'Library', 'Application Support', 'ttmp32gme', 'library'))->stringify;
	if ( ! -d $library ){
		make_path($library);
	}
	return $library;
}

sub loadTemplates {
	my %templates = ();
	$templates{'base'} = Text::Template->new(TYPE => 'STRING',  SOURCE => PAR::read_file('base.html'));
	$templates{'config'} = Text::Template->new(TYPE => 'STRING',  SOURCE => PAR::read_file('config.html'));
	
	return %templates;
}

sub loadAssets {
	my %assets = ();
	my $manifest = PAR::read_file('assets.list');
	open my $fh, '<', \$manifest;
	while(my $path = <$fh>) {
		chomp $path;
		my $content = loadFile($path);
		my $mime;
		if ( $path =~ /.js$/ ) {
			$mime = 'text/javascript';
		} elsif ( $path =~ /.css$/ ) {
			$mime = 'text/css';
		} else {
			$mime = '';
		}
		$assets{"/".$path} = sub {
		my ($httpd, $req) = @_;

		$req->respond({ content => [$mime, $content] });
		}
	}
	
	
	return %assets;
}

sub checkConfigFile {
	my $configdir = (dir($ENV{'HOME'} , 'Library', 'Application Support', 'ttmp32gme'))->stringify;
	if ( ! -d $configdir ){
		make_path($configdir);
	}
	
	my $configfile = (file($configdir, 'config.sqlite'))->stringify;
	if(! -f $configfile){
		my $cfgToCopy = (file($ENV{'PAR_TEMP'}, 'inc', 'config.sqlite'))->stringify;
		copy($cfgToCopy, $configfile);
	}
	
	return $configfile;
}

sub openBrowser {
	my %config = @_;
	`open http://127.0.0.1:$config{'port'}/`;
	return 1;
}

1;
