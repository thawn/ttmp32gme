package TTMp32Gme::Build::FileHandler;

use strict;
use warnings;

use PAR;
use Path::Class;

require Exporter;
our @ISA = qw(Exporter);
our @EXPORT =
	qw(loadTemplates loadAssets openBrowser getLibraryPath checkConfigFile loadStatic makeTempAlbumDir makeNewAlbumDir moveToAlbum removeTempDir clearAlbum removeAlbum cleanup_filename remove_library_dir get_executable_path get_oid_cache get_tiptoi_dir);

my @build_imports =
	qw(loadFile get_local_storage get_par_tmp loadTemplates loadAssets openBrowser);

if ( PAR::read_file('build.txt') ) {
	if ( $^O eq 'darwin' ) {
		require TTMp32Gme::Build::Mac;
		import TTMp32Gme::Build::Mac @build_imports;
	} elsif ( $^O =~ /MSWin/ ) {
		require TTMp32Gme::Build::Win;
		import TTMp32Gme::Build::Win @build_imports;
	}
} else {
	require TTMp32Gme::Build::Perl;
	import TTMp32Gme::Build::Perl @build_imports;
}

## private functions:

sub get_unique_path {
	my ($path) = @_;
	my $count = 0;
	while ( -e $path ) {
		$path =~ s/_\d*$//;
		$path .= '_' . $count;
		$count++;
	}
	return $path;
}

##public functions:

sub getLibraryPath {
	my $library = dir( get_local_storage(), 'library' );
	$library->mkpath();
	return $library->stringify();
}

sub checkConfigFile {
	my $configdir = get_local_storage();
	my $configfile = file( $configdir, 'config.sqlite' );
	if ( !-f $configfile ) {
		my $cfgToCopy = file( get_par_tmp(), 'config.sqlite' );
		$cfgToCopy->copy_to($configfile)
			or die "Could not create local copy of config file '$cfgToCopy': $!";
	}
	return $configfile;
}

sub loadStatic {
	my $static = {};
	my @staticFiles = ( 'upload.html', 'library.html', 'help.html', );
	foreach my $file (@staticFiles) {
		$static->{$file} = loadFile($file);
	}

	return $static;
}

sub makeTempAlbumDir {
	my $albumPath = dir( getLibraryPath(), 'temp', $_[0] );
	$albumPath->mkpath();
	return $albumPath;
}

sub makeNewAlbumDir {
	my $albumTitle = $_[0];

	#make sure no album hogs the temp directory
	if ( $albumTitle eq 'temp' ) {
		$albumTitle .= '_0';
	}
	my $album_path =
		get_unique_path( ( dir( getLibraryPath(), $albumTitle ) )->stringify );
	$album_path = dir($album_path);
	$album_path->mkpath();
	return $album_path->stringify;
}

sub moveToAlbum {
	my ( $albumPath, $filePath ) = @_;
	my $file = file($filePath);
	my $target =
		get_unique_path(
		file( $albumPath, cleanup_filename( $file->basename() ) )->stringify );
	my $target_file = file($target);
	my $album_file  = $file->move_to($target_file);
	return $album_file->basename();
}

sub removeTempDir {
	my $tempPath = dir( getLibraryPath(), 'temp' );
	if ( $tempPath =~ /temp/ && -d $tempPath ) {
		print "deleting $tempPath\n";
		$tempPath->rmtree();
	}
	return 1;
}

sub clearAlbum {
	my ( $path, $file_list ) = @_;
	my $libraryPath = getLibraryPath();
	$libraryPath =~ s/\\/\\\\/g;    #fix windows paths
	if ( $path =~ /^$libraryPath/ ) {
		foreach my $file ( @{$file_list} ) {
			if ($file) {
				my $full_file = file( $path, $file );
				if ( -f $full_file ) {
					$full_file->remove();
				}
			}
		}
		return 1;
	} else {
		return 0;
	}
}

sub removeAlbum {
	my ($path) = @_;
	my $libraryPath = getLibraryPath();
	$libraryPath =~ s/\\/\\\\/g;    #fix windows paths
	if ( $path =~ /^$libraryPath/ ) {
		( dir($path) )->rmtree();
		return 1;
	} else {
		return 0;
	}
}

sub cleanup_filename {
	my $filename = $_[0];
	$filename =~ s/\s/_/g;
	$filename =~ s/[^A-Za-z0-9_\-\.]//g;
	$filename =~ s/\.\./\./g;
	$filename =~ s/\.$//g;
	return $filename;
}

sub remove_library_dir {
	my ($media_path) = @_;
	my $media_dir    = dir($media_path);
	my $libraryPath  = getLibraryPath();
	$libraryPath =~ s/\\/\\\\/g;    #fix windows paths
	if ( $media_dir =~ /^$libraryPath/ ) {
		$media_dir->rmtree();
		return 1;
	} else {
		return 0;
	}
}

sub get_executable_path {
	my $exe_name = $_[0];
	if ( $^O =~ /MSWin/ ) {
		$exe_name .= '.exe';
	}
	my $exe_path;
	if ( PAR::read_file('build.txt') ) {
		$exe_path = ( file( get_par_tmp(), 'lib', $exe_name ) )->stringify();
	} else {
		if ( $^O =~ /MSWin/ ) {
			$exe_path =
				( file( get_par_tmp(), '..', 'lib', 'win', $exe_name ) )->stringify();
		} elsif ( $^O eq 'darwin' ) {
			$exe_path =
				( file( get_par_tmp(), '..', 'lib', 'mac', $exe_name ) )->stringify();
		} else {
			$ENV{'PATH'} = $ENV{'PATH'} . ':/usr/local/bin';
			my $foo = `which $exe_name`;
			chomp($foo);
			$exe_path = $foo;
		}
	}
	if ( -x $exe_path ) {
		return $exe_path;
	} else {
		return "";
	}
}

sub get_oid_cache {
	my $oid_cache = dir( get_local_storage(), 'oid_cache' );
	if ( !-d $oid_cache ) {
		$oid_cache->mkpath();
		my $cache = dir( get_par_tmp(), 'oid_cache' );
		$cache->recurse(
			callback => sub {
				my ($file) = @_;
				if ( -f $file && $file =~ /\.png$/ ) {
					$file->copy_to( file( $oid_cache, $file->basename() ) );
				}
			}
		);
	}
	return $oid_cache->stringify();
}

sub get_tiptoi_dir {
	if ( $^O eq 'darwin' ) {
		my @tiptoi_paths =
			( dir( '', 'Volumes', 'tiptoi' ), dir( '', 'Volumes', 'TIPTOI' ) );
		foreach my $tiptoi_path (@tiptoi_paths) {
			if ( -w $tiptoi_path ) {
				return $tiptoi_path;
			}
		}
	} elsif ( $^O =~ /MSWin/ ) {
		require Win32API::File;
		my @drives = Win32API::File::getLogicalDrives();
		foreach my $d (@drives) {
			my @info = (undef) x 7;
			Win32API::File::GetVolumeInformation( $d, @info );
			if ( lc $info[0] eq 'tiptoi' ) {
				return $d;
			}
		}
	} else {
		my @mount_points = (
			'/mnt/tiptoi',             "/media/$ENV{'USER'}/tiptoi",
			'/media/removable/tiptoi', "/media/$ENV{'USER'}/TIPTOI",
			'/media/removable/TIPTOI'
		);
		foreach my $mount_point (@mount_points) {
			if ( -f "$mount_point/tiptoi.ico" ) {
				return $mount_point;
			}
		}
	}
	return 0;
}

1;
