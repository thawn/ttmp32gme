package TTMp32Gme::TttoolHandler;

use strict;
use warnings;

use Path::Class;
use Cwd;

use Log::Message::Simple qw(msg error);

use TTMp32Gme::Build::FileHandler;
use TTMp32Gme::LibraryHandler;

require Exporter;
our @ISA    = qw(Exporter);
our @EXPORT = qw(get_sorted_tracks make_gme generate_oid_images create_oids copy_gme);

## internal functions:

sub generate_codes_yaml {
	my ( $yaml_file, $dbh ) = @_;
	my $fh = $yaml_file->openr();

	#first seek to the scripts section
	while ( my $row = <$fh> ) {
		if ( $row =~ /scripts:/ ) {
			last;
		}
	}
	my @scripts;
	while ( my $row = <$fh> ) {
		$row =~ s/\s*(.*)\R/$1/g;
		if ( $row =~ /:$/ ) {
			$row =~ s/://;
			push( @scripts, $row );
		}
	}
	close($fh);
	my $query = "SELECT * FROM script_codes";
	my $codes = $dbh->selectall_hashref( $query, 'script' );

	my @sorted_codes;
	foreach my $script ( keys %{$codes} ) {
		push( @sorted_codes, $codes->{$script}{'code'} );
	}

	@sorted_codes = sort { $b <=> $a } @sorted_codes;
	my $last_code = $sorted_codes[0];

	my $filename = $yaml_file->basename();
	$filename =~ s/yaml$/codes.yaml/;
	my $codes_file = file( $yaml_file->dir(), $filename );
	$fh = $codes_file->openw();
	print $fh '# This file contains a mapping from script names to oid codes.
# This way the existing scripts are always assigned to the the
# same codes, even if you add further scripts.
# 
# You can copy the contents of this file into the main .yaml file,
# if you want to have both together.
# 
# If you delete this file, the next run of "ttool assemble" might
# use different codes for your scripts, and you might have to re-
# create the images for your product.
scriptcodes:
';
	foreach my $script (@scripts) {
		if ( $codes->{$script}{'code'} ) {
			print $fh "  $script: $codes->{$script}{'code'}\n";
		} else {
			$last_code++;
			if ( $last_code > 14999 ) {
				my %code_test = map { $_ => 1 } @sorted_codes;
				$last_code = 1001;
				while ( $code_test{$last_code} ) {
					$last_code++;
				}
				if ( $last_code > 14999 ) {
					die("Cannot create script. All script codes are used up.");
				}
			}
			my $qh = $dbh->prepare(q(INSERT INTO script_codes VALUES (?,?) ));
			$qh->execute( ( $script, $last_code ) );
			unshift( @sorted_codes, $last_code );
			$codes->{$script}{'code'} = $last_code;
			print $fh "  $script: $last_code\n";
		}
	}
	close($fh);
	return $codes_file;
}

sub convert_tracks {
	my ( $album, $yaml_file, $config, $dbh ) = @_;
	my $media_path = dir( $album->{'path'}, "audio" );
	my @tracks     = get_sorted_tracks($album);

	$media_path->mkpath();
	if ( $config->{'audio_format'} eq 'ogg' ) {
		my $ff_command = get_executable_path('ffmpeg');
		foreach my $i ( 0 .. $#tracks ) {
			my $source_file =
				file( $album->{'path'}, $album->{ $tracks[$i] }->{'filename'} );
			my $target_file = file( $media_path, "track_$i.ogg" );
			`$ff_command -i '$source_file' -ar 22050 -ac 1 '$target_file'`;
		}
	} else {
		foreach my $i ( 0 .. $#tracks ) {
			file( $album->{'path'}, $album->{ $tracks[$i] }->{'filename'} )->copy_to( file( $media_path, "track_$i.mp3" ) );
		}
	}
	my $next = "  next:\n";
	my $prev = "  prev:\n";
	my $play = "  play:\n";
	my $track_scripts;

	foreach my $i ( 0 .. $#tracks ) {
		if ( $i < $#tracks ) {
			$play .= "  - \$current==$i? P(@{[$i]})";
			$play .= $album->{'player_mode'} eq 'tiptoi' ? " C\n" : " J(t@{[$i+1]})\n";
			if ( $i < $#tracks - 1 ) {
				$next .= "  - \$current==$i? \$current:=@{[$i+1]} P(@{[$i+1]})";
				$next .= $album->{'player_mode'} eq 'tiptoi' ? " C\n" : " J(t@{[$i+2]})\n";
			} else {
				$next .= "  - \$current==$i? \$current:=@{[$i+1]} P(@{[$i+1]}) C\n";
			}
		} else {
			$play .= "  - \$current==$i? P(@{[$i]}) C\n";
		}
		if ( $i > 0 ) {
			$prev .= "  - \$current==$i? \$current:=@{[$i-1]} P(@{[$i-1]})";
			$prev .= $album->{'player_mode'} eq 'tiptoi' ? " C\n" : " J(t@{[$i]})\n";
		}
		if ( $i < $#tracks ) {
			$track_scripts .= "  t$i:\n  - \$current:=$i P($i)";
			$track_scripts .= $album->{'player_mode'} eq 'tiptoi' ? " C\n" : " J(t@{[$i+1]})\n";
		} else {
			$track_scripts .= "  t$i:\n  - \$current:=$i P($i) C\n";
		}
		my %data      = ( 'tt_script' => "t$i" );
		my @selectors = ( $album->{ $tracks[$i] }->{'parent_oid'}, $album->{ $tracks[$i] }->{'track'} );
		updateTableEntry( 'tracks', 'parent_oid=? and track=?', \@selectors, \%data, $dbh );
	}
	my $lastTrack = $#tracks;
	if ( scalar @tracks < $config->{'print_max_track_controls'} ) {

		#in case we use general track controls, we just play the last available
		#track if the user selects a track number that does not exist in this album.
		foreach my $i ( scalar @tracks .. $config->{'print_max_track_controls'} - 1 ) {
			$track_scripts .= "  t$i:\n  - \$current:=$lastTrack P($lastTrack) C\n";
		}
	}
	my $welcome;
	if ( $#tracks == 0 ) {

		#if there is only one track, the next and prev buttons just play that track.
		$next .= "  - \$current:=$lastTrack P($lastTrack) C\n";
		$prev .= "  - \$current:=$lastTrack P($lastTrack) C\n";
		$play .= "  - \$current:=$lastTrack P($lastTrack) C\n";
		$welcome = "welcome: " . "'$lastTrack'" . "\n";
	} else {
		$welcome =
			$album->{'player_mode'} eq 'tiptoi'
			? "welcome: " . "'0'" . "\n"
			: "welcome: " . join( ', ', ( 0 .. $#tracks ) ) . "\n";

	}

	# add track code to the yaml file:
	my $fh = $yaml_file->opena();

	print $fh "media-path: audio/track_%s\n";
	print $fh "init: \$current:=0\n";
	print $fh $welcome;
	print $fh "scripts:\n";
	print $fh $play;
	print $fh $next;
	print $fh $prev;
	print $fh "  stop:\n  - C C\n";
	print $fh $track_scripts;
	close($fh);
	return $media_path;
}

sub get_tttool_parameters {
	my ($dbh) = @_;
	my $tt_params =
		$dbh->selectall_hashref( q(SELECT * FROM config WHERE param LIKE 'tt\_%' ESCAPE '\' AND value IS NOT NULL),
		'param' );
	my %formatted_parameters;
	foreach my $param ( keys %{$tt_params} ) {
		my $parameter = $param;
		$parameter =~ s/^tt_//;
		$formatted_parameters{$parameter} = $tt_params->{$param}{'value'};
	}
	return \%formatted_parameters;
}

sub get_tttool_command {
	my ($dbh)      = @_;
	my $tt_command = get_executable_path('tttool');
	my $tt_params  = get_tttool_parameters($dbh);
	foreach my $param ( sort keys %{$tt_params} ) {
		$tt_command .= " --$param $tt_params->{$param}";
	}
	return $tt_command;
}

sub run_tttool {
	my ( $arguments, $path, $dbh ) = @_;
	my $maindir = cwd();
	if ($path) {
		chdir($path) or die "Can't open '$path': $!";
	}
	my $tt_command = get_tttool_command($dbh);
	print "$tt_command $arguments\n";
	my $tt_output = `$tt_command $arguments`;
	chdir($maindir);
	if ($?) {
		error( $tt_output, 1 );
		return 0;
	} else {
		msg( $tt_output, 1 );
		return 1;
	}
}

##exported functions

sub get_sorted_tracks {
	my ($album) = @_;

	#need to jump through some hoops here to get proper numeric sorting:
	my @tracks = grep { $_ =~ /^track_/ } keys %{$album};
	@tracks = sort { $a <=> $b } map { $_ =~ s/^track_//r } @tracks;
	@tracks = map  { 'track_' . $_ } @tracks;
	return @tracks;
}

sub make_gme {
	my ( $oid, $config, $dbh ) = @_;
	my $album = get_album( $oid, $dbh );
	$album->{'old_oid'} = $oid;
	my $yaml_file = file( $album->{'path'}, sprintf( '%s.yaml', cleanup_filename( $album->{'album_title'} ) ) );
	my $fh        = $yaml_file->openw();
	print $fh "#this file was generated automatically by ttmp32gme\n";
	print $fh "product-id: $oid\n";
	if ( $config->{'pen_language'} ne 'GERMAN' ) {
		print $fh "gme-lang: $config->{'pen_language'}\n";
	}
	close($fh);
	my $media_path = convert_tracks( $album, $yaml_file, $config, $dbh );
	my $codes_file = generate_codes_yaml( $yaml_file, $dbh );
	my $yaml       = $yaml_file->basename();

	if ( run_tttool( "assemble $yaml", $album->{'path'}, $dbh ) ) {
		my $gme_filename = $yaml_file->basename();
		$gme_filename =~ s/yaml$/gme/;
		my %data     = ( 'gme_file' => $gme_filename );
		my @selector = ($oid);
		updateTableEntry( 'gme_library', 'oid=?', \@selector, \%data, $dbh );
	}
	remove_library_dir( $media_path, $config->{'library_path'} );
	return $oid;
}

sub create_oids {
	my ( $oids, $size, $dbh ) = @_;
	my $target_path = get_oid_cache();
	my $tt_params   = get_tttool_parameters($dbh);
	my @files;
	my $tt_command = " --code-dim " . $size . " oid-code ";
	foreach my $oid ( @{$oids} ) {
		my $oid_file = file( $target_path, "$oid-$size-$tt_params->{'dpi'}-$tt_params->{'pixel-size'}.png" );
		if ( !-f $oid_file ) {
			run_tttool( $tt_command . $oid, "", $dbh )
				or die "Could not create oid file: $!";
			file("oid-$oid.png")->move_to($oid_file);
		}
		push( @files, $oid_file );
	}
	return \@files;
}

sub copy_gme {
	my ( $oid, $config, $dbh ) = @_;
	my $album_data = $dbh->selectrow_hashref( q(SELECT path,gme_file FROM gme_library WHERE oid=?), {}, $oid );
	if ( !$album_data->{'gme_file'} ) {
		make_gme( $oid, $config, $dbh );
		$album_data = $dbh->selectrow_hashref( q(SELECT path,gme_file FROM gme_library WHERE oid=?), {}, $oid );
	}
	my $gme_file   = file( $album_data->{'path'}, $album_data->{'gme_file'} );
	my $tiptoi_dir = get_tiptoi_dir();
	msg( "Copying $album_data->{'gme_file'} to $tiptoi_dir", 1 );
	$gme_file->copy_to( file( $tiptoi_dir, $gme_file->basename() ) );
	msg( "done.", 1 );
	return $oid;
}

1;
