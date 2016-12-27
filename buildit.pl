#!/usr/bin/env perl


# Building with pp does NOT WORK with perl v5.10.0
#  v5.10.0 will produce strange behavior in PAR applications
#  Use Perl v5.10.1 and above only.

use File::Copy;
use File::Copy::Recursive qw(fcopy rcopy dircopy);
use Path::Class;
use File::Path qw(make_path remove_tree);
use File::Find;
use Cwd;

my $modulesToAdd = "-M Moose::Meta::Object::Trait -M Package::Stash::XS -M URI::Find";
my $filesToAdd = "";

my $copyTo = (dir( cwd , 'build', 'current' ))->stringify;
my $copyFrom = (dir( cwd ))->stringify;
my $path_sep = '\/';

print "Copying source files into build/current\n\n";

my $assetsList = "";
my $templatesList = "";
$filesToAdd .= " -a assets.list -a templates.list";

find( { wanted => sub {
	if( $_ !~ /^\./ ){
		if( -f (file($copyFrom , $File::Find::name))->stringify ){
			my $toName = $File::Find::name;
			$toName =~ s/^src$path_sep//;
			print "$toName\n";
			rcopy( (file($copyFrom , $File::Find::name))->stringify , (file($copyTo , $toName))->stringify );
			$filesToAdd .= " -a $toName";
			if ($toName =~ /^assets/) {
				$assetsList .= "$toName\n";
			} elsif ($toName =~ /^templates/) {
				$templatesList .= "$toName\n";
			}
		}
	}
} , no_chdir => 0 }, 'src');

my $builddir = (dir('build', 'current'))->stringify;
if ( ! -d $builddir ){
	make_path($builddir);
}

my $fh = (file($copyTo,'assets.list'))->openw();
print $fh $assetsList;
close($fh);

$fh = (file($copyTo,'templates.list'))->openw();
print $fh $templatesList;
close($fh);

if ( $^O =~ /MSWin/ ){
	use Win32::Exe;
	print "\nWindows build.\n\n";
	
	copy((file('build', 'win', 'ttmp32gme.ico'))->stringify, (file($builddir, 'ttmp32gme.ico'))->stringify);
	
	chdir($builddir);
	my $result = `pp -M attributes -M UNIVERSAL $filesToAdd $modulesToAdd -o ttmp32gme.exe ttmp32gme.pl`;
	
	# newer versions of pp don't support the --icon option any more, use Win32::Exe to manually replace the icon:
#	$exe = Win32::Exe->new('ttmp32gme.exe');
#	$exe->set_single_group_icon('ttmp32gme.ico');
#	$exe->write;
	
	print $result;
	if ( $? != 0 ){ die "Build failed.\n"; }
	
	chdir('..\..');
	my $distdir = 'dist';
	if ( ! -d $distdir ){
		make_path($distdir);
	}
	
	fcopy((file($builddir , 'ttmp32gme.exe'))->stringify, (file('dist', 'ttmp32gme.exe'))->stringify);
	`explorer dist`;
	print "Build successful.\n";
	
} elsif ( $^O eq 'darwin' ){
	print "\nMac OS X build.\n\n";
	
	chdir($builddir);
	my $libxml = '-l /usr/lib/libxml2.dylib';
	if( `which brew` ){
		my $brew_xml_dir = `brew --cellar libxml2`;
		$brew_xml_dir =~ s/\n|\r//g;
		if( -d "$brew_xml_dir" ){
			$brew_xml_dir = `brew --prefix libxml2`;
			$brew_xml_dir =~ s/\n|\r//g;
			$libxml = "-l $brew_xml_dir/lib/libxml2.dylib";
		}
	}
	
	my $result = `pp $libxml $filesToAdd $modulesToAdd -o ttmp32gme ttmp32gme.pl`;
	
	print $result;
	if ( $? != 0 ){ die "Build failed.\n"; }
	
	chdir('../..');
	my $distdir = 'dist';
	if ( ! -d $distdir ){
		make_path($distdir);
	}
	
	dircopy((dir('build', 'mac', 'ttmp32gme.app'))->stringify,(dir('dist', 'ttmp32gme.app'))->stringify );
	fcopy((file('build', 'current', 'ttmp32gme'))->stringify, (file('dist', 'ttmp32gme.app', 'Contents', 'Resources', 'ttmp32gme'))->stringify);
	`open dist`;
	print "Build successful.\n";
} else {
	print "Unsupported platform.  Try installing the required perl modules and running the script out of the src folder.\n" .
	"Maybe even send in a patch with a build script for your platform.\n";
}

print "Cleaning build folders.\n";
remove_tree($builddir, {keep_root => 1});

print "Done.\n";
exit(0);

